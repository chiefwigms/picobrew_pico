import json
from datetime import datetime, timedelta
from dateutil import tz
from enum import Enum
from aenum import MultiValueEnum
from pathlib import Path
from flask import current_app

from .config import (brew_active_sessions_path, ferm_active_sessions_path, still_active_sessions_path,
                     iSpindel_active_sessions_path, tilt_active_sessions_path, brew_archive_sessions_path,
                     MachineType)
from .model import PicoBrewSession, PicoFermSession, PicoStillSession, iSpindelSession, TiltSession

file_glob_pattern = "[!._]*.json"

active_brew_sessions = {}
active_ferm_sessions = {}
active_still_sessions = {}
active_iSpindel_sessions = {}
active_tilt_sessions = {}

invalid_sessions = {}


def load_session_file(filename):
    json_data = {}
    try:
        with open(filename) as fp:
            raw_data = fp.read().rstrip()
            session = recover_incomplete_session(raw_data, filename)
            json_data = json.loads(session)
    except Exception as e:
        current_app.logger.error("An exception occurred parsing session file {}".format(filename))
        current_app.logger.error(e)

    return json_data


def recover_incomplete_session(raw_data, filename):
    # attempt to recover various incomplete session files
    # (raw_data is already rstrip() so no trailing whitespace)
    recovered_session = raw_data
    if raw_data == None or raw_data.endswith('[') or raw_data == '':
        # aborted session data file (containing no datalog entries)
        recovered_session = '[\n]'
    elif raw_data.endswith(',\n]'):
        # closed trailing comma in datalog
        recovered_session = raw_data[:-3] + '\n]\n'
    elif raw_data.endswith(',\n\n]'):
        # closed trailing comma and extra newline in datalog
        recovered_session = raw_data[:-4] + '\n]\n'
    elif raw_data.endswith('}'):
        # unclosed array of data entries
        recovered_session = raw_data + '\n]\n'
    elif raw_data.endswith(','):
        # open trailing comma
        recovered_session = raw_data[:-1] + '\n]\n'
    elif raw_data.endswith('\x00'):
        # corrupted file (trailing nulls with open comma)
        recovered_session = raw_data.rstrip("\x00")[:-1] + '\n]\n'

    return recovered_session


def load_brew_session(file):
    info = file.stem.split('#')

    # 0 = Date, 1 = UID, 2 = RFID / Session GUID (guid), 3 = Session Name, 4 = Session Type (integer - z only)
    json_data = load_session_file(file)

    # unencode the name section ('_' => ' ' ; '%23' -> '#')
    name = info[3].replace('_', ' ').replace("%23", "#")
    step = ''
    chart_id = info[0] + '_' + info[2]
    alias = '' if info[1] not in active_brew_sessions else active_brew_sessions[info[1]].alias

    session_type = None
    if len(info) > 4:
        session_type = int(info[4])

    # filename datetime string format "20200615_205946"
    server_start_datetime = datetime.strptime(info[0], '%Y%m%d_%H%M%S')
    # json datetime `timeStr` format "2020-06-15T20:59:46.280731" (UTC) ; 'time' milliseconds from epoch
    server_end_datetime = datetime.strptime(info[0], '%Y%m%d_%H%M%S')
    if len(json_data) > 0:
        # set server end datetime to last data log entry
        server_end_datetime = epoch_millis_converter(json_data[-1]['time'])

    session = {
        'date': server_start_datetime,
        'end_date': server_end_datetime,
        'name': name,
        'filename': Path(file).name,
        'filepath': Path(file),
        'uid': info[1],
        'session': info[2],
        'is_pico': len(info[1]) == 32,
        'type': session_type,
        'alias': alias,
        'data': json_data,
        'graph': get_brew_graph_data(chart_id, name, step, json_data)
    }
    if len(json_data) > 0:
        if 'recovery' in json_data[-1]:
            session.update({'recovery': json_data[-1]['recovery']})
        if 'timeLeft' in json_data[-1]:
            session.update({'timeLeft': json_data[-1]['timeLeft']})
    return (session)


def get_brew_graph_data(chart_id, session_name, session_step, session_data, is_pico=None):
    wort_data = []  # Shared

    block_data = []  # Pico and ZSeries Only

    board_data = []  # Zymatic Only
    heat1_data = []  # Zymatic Only
    heat2_data = []  # Zymatic Only

    target_data = []  # ZSeries Only
    drain_data = []  # ZSeries Only
    ambient_data = []  # ZSeries Only
    valve_position = []  # ZSeries Only

    events = []
    plot_bands = []
    prev = {}
    for data in session_data:
        if all(k in data for k in ('therm', 'wort')):  # Pico and ZSeries
            wort_data.append([data['time'], int(data['wort'])])
            block_data.append([data['time'], int(data['therm'])])

        if all(k in data for k in ('target', 'drain', 'ambient', 'position')):  # ZSeries
            target_data.append([data['time'], int(data['target'])])
            drain_data.append([data['time'], int(data['drain'])])
            ambient_data.append([data['time'], int(data['ambient'])])
            # TODO figure out how to add `position`, `pause_state` and `error` to the graphs?
            valve_position.append([data['time'], int(data['position'])])

        if all(k in data for k in ('wort', 'board', 'heat1', 'heat2')):  # Zymatic
            wort_data.append([data['time'], int(data['wort'])])
            board_data.append([data['time'], int(data['board'])])
            heat1_data.append([data['time'], int(data['heat1'])])
            heat2_data.append([data['time'], int(data['heat2'])])

        # add an overlay event for each step
        if 'event' in data:
            events.append({
                'color': 'black',
                'value': data['time'],
                'label': {
                    'text': data['event']
                }
            })

        # add an overlay error for each errorCode or pauseReason
        error_code = data['errorCode'] if 'errorCode' in data else 0
        pause_reason = data['pauseReason'] if 'pauseReason' in data else 0
        prev_error_code = prev['errorCode'] if 'errorCode' in prev else 0
        prev_pause_reason = prev['pauseReason'] if 'pauseReason' in prev else 0
        if error_code != 0 or pause_reason != 0:
            new_band = False

            if len(plot_bands) == 0 or error_code != prev_error_code or pause_reason != prev_pause_reason:
                new_band = True

            if new_band:
                plot_bands.append({
                    'from': data.get('time'),
                    'to': None,
                    'label': {
                        'text': reason_phrase(error_code, pause_reason)
                    }
                })
            else:
                plot_bands[-1]['to'] = data.get('time')
        elif prev_error_code != 0 or prev_pause_reason != 0:
            plot_bands[-1]['to'] = prev.get('time')

        prev = data

    # fix plot_band if last data point is pause or error
    if len(plot_bands) > 0 and plot_bands[-1]['to'] == None:
        plot_bands[-1]['to'] = session_data[-1]['time']

    graph_data = {
        'chart_id': chart_id,
        'title': {'text': session_name},
        'subtitle': {'text': session_step},
        'xaplotlines': events,
        'xaplotbands': plot_bands
    }
    if len(ambient_data) > 0:
        graph_data.update({'series': [
            {'name': 'Target', 'data': target_data},
            {'name': 'Wort', 'data': wort_data},
            {'name': 'Heat Exchanger', 'data': block_data},
            {'name': 'Drain', 'data': drain_data},
            {'name': 'Ambient', 'data': ambient_data}
        ]})
    elif len(block_data) > 0 or is_pico:
        graph_data.update({'series': [
            {'name': 'Wort', 'data': wort_data},
            {'name': 'Heat Block', 'data': block_data}
        ]})
    else:
        graph_data.update({'series': [
            {'name': 'Wort', 'data': wort_data},
            {'name': 'Heat Loop (Glycol)', 'data': heat1_data},
            {'name': 'Board', 'data': board_data},
            {'name': 'Heat Loop (Element)', 'data': heat2_data}
        ]})
    return graph_data


def load_ferm_session(file):
    info = file.stem.split('#')

    # 0 = Date, 1 = Device UID
    json_data = load_session_file(file)

    chart_id = info[0] + '_' + info[1]
    name = info[1]
    alias = info[1] if info[1] not in active_ferm_sessions else active_ferm_sessions[info[1]].alias

    # filename datetime string format "20200615_205946"
    server_start_datetime = datetime.strptime(info[0], '%Y%m%d_%H%M%S')
    # json datetime `timeStr` format "2020-06-15T20:59:46.280731" (UTC) ; 'time' milliseconds from epoch
    server_end_datetime = datetime.strptime(info[0], '%Y%m%d_%H%M%S')
    if len(json_data) > 0:
        # set server start datetime to the first data log entry (approx -1hr from session file creation)
        server_start_datetime = epoch_millis_converter(json_data[0]['time'])

        # set server end datetime to last data log entry
        server_end_datetime = epoch_millis_converter(json_data[-1]['time'])

    return ({
        'uid': info[1],
        'filename': Path(file).name,
        'filepath': Path(file),
        'alias': alias,
        'date': server_start_datetime,
        'end_date': server_end_datetime,
        'name': name,  # should change to brew/user defined session name
        'data': json_data,
        'graph': get_ferm_graph_data(chart_id, None, json_data)
    })


# map programmatic codes to user facing strings (displayed in the brew graph)
#
# error codes:
#   4 == Overheat - too hot
#   6 == Overheat - Max HEX Wort Delta
#  12 == PicoStill Error
#
# pause reasons:
#   1 == waiting for user / finished / program
def reason_phrase(error_code, pause_reason):
    reason = ''
    if pause_reason != 0:
        reason += 'pause: '
        if pause_reason == 1:
            reason += 'program'
        if pause_reason == 2:
            reason += 'user'
    elif error_code != 0:
        reason += f'error: {error_code}'

    return reason


def get_ferm_graph_data(chart_id, voltage, session_data):
    temp_data = []
    pres_data = []
    for data in session_data:
        temp_data.append([data['time'], float(data['temp'])])
        pres_data.append([data['time'], float(data['pres'])])
    graph_data = {
        'chart_id': chart_id,
        'title': {'text': 'Fermentation'},
        'series': [
            {
                'name': 'Temperature',
                'data': temp_data
            }, {
                'name': 'Pressure',
                'data': pres_data,
                'yAxis': 1
            }
        ],
    }
    if voltage:
        graph_data.update({'subtitle': {'text': 'Voltage: ' + voltage}})
    return graph_data


def epoch_millis_converter(epoch_ms):
    epoch_s, differential_ms = divmod(epoch_ms, 1000.0)
    datetime_utc = datetime.fromtimestamp(epoch_s, tz.tzutc())
    return datetime_utc.astimezone(tz.tzlocal())


def load_still_session(file):
    info = file.stem.split('#')
    # 0 = Date, 1 = Device UID
    json_data = load_session_file(file)

    chart_id = info[0] + '_' + info[1]
    name = info[1]
    alias = info[1] if info[1] not in active_still_sessions else active_still_sessions[info[1]].alias

    # filename datetime string format "20200615_205946"
    server_start_datetime = datetime.strptime(info[0], '%Y%m%d_%H%M%S')
    # json datetime `timeStr` format "2020-06-15T20:59:46.280731" (UTC) ; 'time' milliseconds from epoch
    server_end_datetime = datetime.strptime(info[0], '%Y%m%d_%H%M%S')
    if len(json_data) > 0:
        # set server end datetime to last data log entry
        server_end_datetime = epoch_millis_converter(json_data[-1]['time'])

    return ({
        'uid': info[1],
        'date': server_start_datetime,
        'filename': Path(file).name,
        'filepath': Path(file),
        'end_date': server_end_datetime,
        'name': name,
        'alias': alias,
        'data': json_data,
        'graph': get_still_graph_data(chart_id, name, json_data)
    })


def get_still_graph_data(chart_id, name, session_data):
    t1_data = []
    t2_data = []
    t3_data = []
    t4_data = []
    pres_data = []
    for data in session_data:
        t1_data.append([data['time'], float(data['t1'])])
        t2_data.append([data['time'], float(data['t2'])])
        t3_data.append([data['time'], float(data['t3'])])
        t4_data.append([data['time'], float(data['t4'])])
        pres_data.append([data['time'], float(data['pres'])])
    graph_data = {
        'chart_id': chart_id,
        'title': {'text': name},
        'series': [
            {
                'name': 'Coil Inlet',
                'data': t1_data
            }, {
                'name': 'Coil Outlet',
                'data': t2_data
            }, {
                'name': 'Pot',
                'data': t3_data
            }, {
                'name': 'Ambient',
                'data': t4_data
            }, {
                'name': 'Pressure',
                'data': pres_data,
                'yAxis': 1
            }
        ],
    }
    return graph_data


def fermentation_graph_subtitle(session_data, voltage=None, rssi=None):
    subtitle_text = ''
    if len(session_data) > 0:
        last_temp = session_data[-1]['temp']
        last_gravity = session_data[-1]['gravity']

        start_datetime = epoch_millis_converter(session_data[0]['time'])
        last_datetime = epoch_millis_converter(session_data[-1]['time'])
        duration_days = round((last_datetime - start_datetime) / timedelta(days=1), 2)
        original_gravity = session_data[0]['gravity']
        standard_abv = round((original_gravity - last_gravity) * 1.3125, 4) # decimal ABV calc (ex. 0.04867);
        abv_pct = round(standard_abv * 100, 2)

        subtitle_text = 'Temperature: ' + str(last_temp) + 'F  |  Specific Gravity: ' + str(last_gravity)
        subtitle_text += '<br>Duration: ' + str(duration_days) + ' Days  |  Approx. ABV: ' + str(abv_pct) + '%'

    if voltage:
        subtitle_text += '<br>Voltage: ' + str(voltage)
        subtitle_text += "V" if voltage != "-" else ""

    if rssi:
        subtitle_text += '<br>RSSI: ' + str(rssi)

    return subtitle_text


def load_iSpindel_session(file):
    info = file.stem.split('#')

    # 0 = Date, 1 = Device UID
    json_data = load_session_file(file)

    chart_id = info[0] + '_' + str(info[1])
    alias = info[1] if info[1] not in active_iSpindel_sessions else active_iSpindel_sessions[info[1]].alias

    # filename datetime string format "20200615_205946"
    server_start_datetime = datetime.strptime(info[0], '%Y%m%d_%H%M%S')
    # json datetime `timeStr` format "2020-06-15T20:59:46.280731" (UTC) ; 'time' milliseconds from epoch
    server_end_datetime = datetime.strptime(info[0], '%Y%m%d_%H%M%S')
    voltage = None
    if len(json_data) > 0:
        # set server start datetime to the first data log entry (approx -1hr from session file creation)
        server_start_datetime = epoch_millis_converter(json_data[0]['time'])

        # set server end datetime to last data log entry
        server_end_datetime = epoch_millis_converter(json_data[-1]['time'])

        # use latest voltage reading
        voltage = json_data[-1].get('battery')

    return ({
        'uid': info[1],
        'filename': Path(file).name,
        'filepath': Path(file),
        'alias': alias,
        'date': server_start_datetime,
        'end_date': server_end_datetime,
        'name': alias,  # should change to brew/user defined session name
        'data': json_data,
        'graph': get_iSpindel_graph_data(chart_id, voltage, json_data)
    })


def get_iSpindel_graph_data(chart_id, voltage, session_data):
    temp_data = []
    gravity_data = []
    for data in session_data:
        temp_data.append([data['time'], float(data['temp'])])
        gravity_data.append([data['time'], float(data['gravity'])])
    graph_data = {
        'chart_id': str(chart_id),
        'title': {'text': 'Fermentation'},
        'subtitle': {'text': fermentation_graph_subtitle(session_data, voltage=voltage)},
        'series': [
            {
                'name': 'Temperature',
                'data': temp_data
            }, {
                'name': 'Specific Gravity',
                'data': gravity_data,
                'yAxis': 1
            }
        ],
    }
    return graph_data


def load_tilt_session(file):
    info = file.stem.split('#')

    # 0 = Date, 1 = Device UID
    json_data = load_session_file(file)

    chart_id = info[0] + '_' + str(info[1])
    alias = info[1] if info[1] not in active_tilt_sessions else active_tilt_sessions[info[1]].alias

    # filename datetime string format "20200615_205946"
    server_start_datetime = datetime.strptime(info[0], '%Y%m%d_%H%M%S')
    # json datetime `timeStr` format "2020-06-15T20:59:46.280731" (UTC) ; 'time' milliseconds from epoch
    server_end_datetime = datetime.strptime(info[0], '%Y%m%d_%H%M%S')
    rssi = None
    if len(json_data) > 0:
        # set server start datetime to the first data log entry (approx -1hr from session file creation)
        server_start_datetime = epoch_millis_converter(json_data[0]['time'])

        # set server end datetime to last data log entry
        server_end_datetime = epoch_millis_converter(json_data[-1]['time'])

        # use latest rssi reading
        rssi = json_data[-1].get('rssi')

    return ({
        'uid': info[1],
        'filename': Path(file).name,
        'filepath': Path(file),
        'alias': alias,
        'date': server_start_datetime,
        'end_date': server_end_datetime,
        'name': alias,  # should change to brew/user defined session name
        'data': json_data,
        'graph': get_tilt_graph_data(chart_id, rssi, json_data)
    })


def get_tilt_graph_data(chart_id, rssi, session_data):
    temp_data = []
    gravity_data = []
    for data in session_data:
        temp_data.append([data['time'], float(data['temp'])])
        gravity_data.append([data['time'], float(data['gravity'])])
    graph_data = {
        'chart_id': str(chart_id),
        'title': {'text': 'Fermentation'},
        'subtitle': {'text': fermentation_graph_subtitle(session_data, rssi=rssi)},
        'series': [
            {
                'name': 'Temperature',
                'data': temp_data
            }, {
                'name': 'Specific Gravity',
                'data': gravity_data,
                'yAxis': 1
            }
        ],
    }
    return graph_data


def restore_active_brew_sessions():
    if active_brew_sessions == {}:
        active_brew_session_files = list(brew_active_sessions_path().glob(file_glob_pattern))
        for file in active_brew_session_files:
            # print('DEBUG: restore_active_sessions() found {} as an active session'.format(file))
            brew_session = load_brew_session(file)
            # print('DEBUG: restore_active_sessions() {}'.format(brew_session))
            uid = brew_session['uid']
            if uid not in active_brew_sessions:
                active_brew_sessions[uid] = PicoBrewSession()

            session = active_brew_sessions[uid]
            session.file = open(file, 'a')
            session.file.flush()
            session.filepath = file
            session.created_at = brew_session['date']
            session.name = brew_session['name']
            session.type = brew_session['type']
            session.session = brew_session['session']                   # session guid
            session.id = -1                                             # session id (integer)

            if 'recovery' in brew_session:
                session.recovery = brew_session['recovery']             # find last step name
                session.step = brew_session['recovery']

            # session.remaining_time = None
            session.data = brew_session['data']

            active_brew_sessions[uid] = session


def restore_active_ferm_sessions():
    if active_ferm_sessions == {}:
        active_ferm_session_files = list(ferm_active_sessions_path().glob(file_glob_pattern))
        for file in active_ferm_session_files:
            # print('DEBUG: restore_active_sessions() found {} as an active session'.format(file))
            ferm_session = load_ferm_session(file)
            # print('DEBUG: restore_active_sessions() {}'.format(ferm_session))
            uid = ferm_session['uid']
            if uid not in active_ferm_sessions:
                active_ferm_sessions[uid] = PicoFermSession()

            session = active_ferm_sessions[uid]
            session.file = open(file, 'a')
            session.file.flush()
            session.filepath = file
            session.start_time = ferm_session['date']
            session.active = True

            session.uninit = False
            session.data = ferm_session['data']
            session.graph = ferm_session['graph']

            active_ferm_sessions[uid] = session


def restore_active_still_sessions():
    if active_still_sessions == {}:
        active_still_session_files = list(still_active_sessions_path().glob(file_glob_pattern))
        for file in active_still_session_files:
            # print('DEBUG: restore_active_sessions() found {} as an active session'.format(file))
            still_session = load_still_session(file)
            # print('DEBUG: restore_active_sessions() {}'.format(still_session))
            uid = still_session['uid']
            if uid not in active_still_sessions:
                active_still_sessions[uid] = PicoStillSession(uid)

            session = active_still_sessions[uid]
            session.file = open(file, 'a')
            session.file.flush()
            session.filepath = file
            session.alias = still_session['alias']
            session.start_time = still_session['date']
            session.active = False

            session.data = still_session['data']
            session.graph = still_session['graph']
            active_still_sessions[uid] = session


def restore_active_iSpindel_sessions():
    if active_iSpindel_sessions == {}:
        active_iSpindel_session_files = list(iSpindel_active_sessions_path().glob(file_glob_pattern))
        for file in active_iSpindel_session_files:
            # print('DEBUG: restore_active_sessions() found {} as an active session'.format(file))
            iSpindel_session = load_iSpindel_session(file)
            # print('DEBUG: restore_active_sessions() {}'.format(ferm_session))
            uid = iSpindel_session['uid']
            if uid not in active_iSpindel_sessions:
                active_iSpindel_sessions[uid] = iSpindelSession()

            session = active_iSpindel_sessions[uid]
            session.file = open(file, 'a')
            session.file.flush()
            session.filepath = file
            session.start_time = iSpindel_session['date']
            session.active = True

            session.uninit = False
            session.data = iSpindel_session['data']
            session.graph = iSpindel_session['graph']

            active_iSpindel_sessions[uid] = session


def restore_active_tilt_sessions():
    if active_tilt_sessions == {}:
        active_tilt_session_files = list(tilt_active_sessions_path().glob(file_glob_pattern))
        for file in active_tilt_session_files:
            # print('DEBUG: restore_active_sessions() found {} as an active session'.format(file))
            tilt_session = load_tilt_session(file)
            # print('DEBUG: restore_active_sessions() {}'.format(ferm_session))
            uid = tilt_session['uid']
            if uid not in active_tilt_sessions:
                active_tilt_sessions[uid] = TiltSession()

            session = active_tilt_sessions[uid]
            session.file = open(file, 'a')
            session.file.flush()
            session.filepath = file
            session.start_time = tilt_session['date']
            session.active = True

            session.uninit = False
            session.data = tilt_session['data']
            session.graph = tilt_session['graph']

            active_tilt_sessions[uid] = session


def restore_active_sessions():
    # initialize active sessions during start up
    restore_active_brew_sessions()
    restore_active_ferm_sessions()
    restore_active_still_sessions()
    restore_active_iSpindel_sessions()
    restore_active_tilt_sessions()


def get_invalid_sessions(sessionType):
    global invalid_sessions
    return invalid_sessions.get(sessionType, set())


def add_invalid_session(sessionType, file):
    global invalid_sessions
    if sessionType not in invalid_sessions:
        invalid_sessions[sessionType] = set()
    invalid_sessions.get(sessionType).add(file)


def parse_brew_session(file):
    try:
        return load_brew_session(file)
    except Exception as e:
        current_app.logger.error("An exception occurred parsing {}".format(file))
        current_app.logger.error(e)
        add_invalid_session("brew", file)


def sampling(selection, offset=0, limit=None):
    return selection[offset:(limit + offset if limit is not None else None)]


def _paginate_sessions(sessions, offset=0, limit=None):
    sessions = sampling(sessions, offset, limit)

    # if pagination request and no sessions found return error
    if (offset != 0 and len(sessions) == 0):
        msg = "unable to paginate sessions to offset={}&limit={}".format(offset, limit)
        current_app.logger.error(msg)
        raise Exception(msg)

    return sessions


def load_brew_sessions(uid=None, offset=0, limit=None):
    files = list_session_files(brew_archive_sessions_path(), uid)

    brew_sessions = [parse_brew_session(file) for file in files]
    brew_sessions = list(filter(lambda x: x != None, brew_sessions))

    return _paginate_sessions(brew_sessions, offset, limit)


def list_session_files(session_path, uid=None, reverse=True):
    files = []
    if uid:
        files = list(session_path.glob("*#{}*.json".format(uid)))
    else:
        files = list(session_path.glob(file_glob_pattern))

    return sorted(files, reverse=reverse)


class ZSessionType(int, Enum):
    RINSE = 0
    CLEAN = 1
    DRAIN = 2
    RACK_BEER = 3
    CIRCULATE = 4
    SOUS_VIDE = 5
    BEER = 6
    STILL = 11
    COFFEE = 12
    CHILL = 13
    MANUAL = 14


class ZProgramId(int, Enum):
    RINSE = 1
    DRAIN = 2
    RACK_BEER = 3
    CIRCULATE = 4
    SOUS_VIDE = 6
    CLEAN = 12
    BEER_OR_COFFEE = 24
    STILL = 26
    CHILL = 27


class PicoSessionType(str, MultiValueEnum):
    RINSE = "RINSE"
    CLEAN = "CLEAN", "DEEP_CLEAN", "DEEP CLEAN"
    DRAIN = "DRAIN"
    RACK_BEER = "RACK"
    MANUAL = "MANUAL"
    BEER = "BEER"

    @classmethod
    def _missing_value_(cls, value):
        for member in cls:
            for _value in member._values_:
                if _value.lower() == value.lower():
                    return member


class BrewSessionType(str, MultiValueEnum):
    RINSE = "RINSE"
    CLEAN = "CLEAN",
    UTILITY = "RACK_BEER", "RACK BEER", "CIRCULATE", "CHILL", "SOUS_VIDE", "SOUS VIDE", "DRAIN"
    MANUAL = "MANUAL"
    BEER = "BEER"
    STILL = "STILL"
    COFFEE = "COFFEE"


def dirty_sessions_since_clean(uid, mtype):
    brew_session_files = list_session_files(brew_archive_sessions_path(), uid)
    post_clean_sessions = []
    clean_found = False

    for s in brew_session_files:
        if mtype == MachineType.PICOBREW_C or MachineType.PICOBREW:
            session_name = session_name_from_filename(s)

            if (session_name.upper() in ["CLEAN", "DEEP CLEAN"]):
                clean_found = True

            if (not clean_found and session_name.upper() not in ["RINSE", "CLEAN", "DEEP CLEAN", "RACK", "DRAIN"]):
                post_clean_sessions.append(s)

        elif mtype == MachineType.ZSERIES:
            session_type = ZSessionType(session_type_from_filename(s))
            if (session_type == ZSessionType.CLEAN):
                clean_found = True

            if (not clean_found and session_type in [ZSessionType.BEER.value, ZSessionType.COFFEE.value, ZSessionType.SOUS_VIDE.value]):
                post_clean_sessions.append(s)

    return len(post_clean_sessions)


def last_session_type(uid, mtype):
    session_type, _ = last_session_metadata(uid, mtype)
    return session_type


def last_session_metadata(uid, mtype):
    brew_sessions = list_session_files(brew_archive_sessions_path(), uid)

    if len(brew_sessions) == 0:
        if mtype == MachineType.ZSERIES:
            return ZSessionType.CLEAN, 'N/A'
        else:
            return PicoSessionType.CLEAN, 'N/A'
    else:
        last_session = brew_sessions[0]
        stype = session_type_from_filename(last_session, mtype)
        sname = session_name_from_filename(last_session)
        if mtype == MachineType.ZSERIES:
            try:
                stype = ZSessionType(stype)
            except Exception as err:
                stype = ZSessionType(0)  # zseries has type enum, assume unmatched to be non-dirty session
            return stype, sname
        else:
            try:
                stype = PicoSessionType(sname)
            except Exception as err:
                # current_app.logger.warn("unknown session type {} - {}".format(sname, err))
                stype = PicoSessionType.BEER  # pico only has name in file (no type enum)
            return stype, sname


def increment_session_id(uid):
    return len(list_session_files(brew_archive_sessions_path(), uid)) + (1 if active_brew_sessions[uid].session != '' else 1)


def get_machine_by_session(session_id):
    return next((uid for uid in active_brew_sessions if active_brew_sessions[uid].session == session_id or active_brew_sessions[uid].id == int(session_id) or active_brew_sessions[uid].id == -1), None)


def get_archived_sessions_by_machine(uid):
    brew_sessions = load_brew_sessions(uid=uid)
    return brew_sessions


def session_type_from_filename(filename, mtype):
    info = filename.stem.split('#')

    session_type = ZSessionType.BEER

    if mtype == MachineType.ZSERIES:
        try:
            if len(info) > 4:
                session_type = int(info[4])
        except Exception as error:
            current_app.logger.warn("error occurred extracting session type from {}".format(filename))

    else:
        session_type = PicoSessionType.BEER
        try:
            if len(info) > 3:
                session_type = PicoSessionType(info[3])
        except Exception as error:
            pass
            # current_app.logger.warn("error occurred extracting session type from {}".format(filename))
            # info[3] is recipe name, utilities == session_type; beer recipe != session_type

    return session_type


def session_name_from_filename(filename):
    info = filename.stem.split('#')
    name = "N/A"
    try:
        if len(info) >= 3:
            name = info[3].replace('_', ' ').replace("%23", "#")
    except Exception as error:
        current_app.logger.warn("error occurred extracting session name from {}".format(filename))
    return name
