import json

from .config import brew_active_sessions_path
from .model import PicoBrewSession

active_brew_sessions = {}
active_ferm_sessions = {}


def load_brew_session(file):
    info = file.stem.split('#')

    # 0 = Date, 1 = UID, 2 = RFID / Session GUID (guid), 3 = Session Name, 4 = Session Type (integer - z only)
    name = info[3].replace('_', ' ')

    step = ''
    with open(file) as fp:
        raw_data = fp.read().rstrip()
        if raw_data.endswith(','):
            # Recover from incomplete session json data file
            raw_data = raw_data[:-1] + '\n]'
        elif raw_data.endswith('[') or raw_data == '':
            # Recover from aborted session data file
            raw_data = '[\n]'
        json_data = json.loads(raw_data)
    chart_id = info[0] + '_' + info[2]

    alias = '' if info[1] not in active_brew_sessions else active_brew_sessions[info[1]].alias

    session_type = None
    if len(info) > 4:
        session_type = int(info[4])

    session = {
        'date': info[0],
        'name': name,
        'uid': info[1],
        'session': info[2],
        'is_pico': len(info[1]) == 32,
        'type': session_type,
        'alias': alias,
        'data': json_data,
        'graph': get_brew_graph_data(chart_id, name, step, json_data)
    }
    if len(json_data) > 0 and 'recovery' in json_data[-1]:
        session.update({'recovery': json_data[-1]['recovery']})
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
            events.append({'color': 'black', 'width': '2', 'value': data['time'],
                           'label': {'text': data['event'], 'style': {'color': 'white', 'fontWeight': 'bold'},
                                     'verticalAlign': 'top', 'x': -15, 'y': 0}})

    graph_data = {
        'chart_id': chart_id,
        'title': {'text': session_name},
        'subtitle': {'text': session_step},
        'xaplotlines': events
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
            {'name': 'Heat Loop', 'data': heat1_data},
            {'name': 'Wort', 'data': wort_data},
            {'name': 'Board', 'data': board_data},
            {'name': 'Heat Loop 2', 'data': heat2_data}
        ]})
    return graph_data


def load_ferm_session(file):
    info = file.stem.split('#')
    # 0 = Date, 1 = Device UID
    with open(file) as fp:
        raw_data = fp.read().rstrip()
        if raw_data.endswith(','):
            # Recover from incomplete json data file
            raw_data = raw_data[:-1] + '\n]'
        json_data = json.loads(raw_data)
    chart_id = info[0] + '_' + info[1]
    name = info[1]
    if info[1] in active_ferm_sessions:
        name = active_ferm_sessions[info[1]].alias
    return ({
        'date': info[0],
        'name': name,
        'graph': get_ferm_graph_data(chart_id, None, json_data)
    })


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


def restore_active_sessions():
    # initialize active sessions during start up
    if active_brew_sessions == {}:
        # print('DEBUG: restore_active_sessions() fetching abandoned server active sessions')

        active_brew_session_files = list(brew_active_sessions_path().glob("*.json"))
        for file in active_brew_session_files:
            # print('DEBUG: restore_active_sessions() found {} as an active session'.format(file))
            brew_session = load_brew_session(file)
            # print('DEBUG: restore_active_sessions() {}'.format(brew_session))
            if brew_session['uid'] not in active_brew_sessions:
                active_brew_sessions[brew_session['uid']] = []

            session = PicoBrewSession()
            session.file = open(file, 'a')
            session.file.flush()
            session.filepath = file
            session.alias = brew_session['alias']
            session.created_at = brew_session['date']
            session.name = brew_session['name']
            session.type = brew_session['type']
            session.session = brew_session['session']           # session guid
            session.id = -1                                     # session id (integer)

            if 'recovery' in brew_session:
                session.recovery = brew_session['recovery']     # find last step name

            # session.remaining_time = None
            session.is_pico = brew_session['is_pico']
            session.data = brew_session['data']
            active_brew_sessions[brew_session['uid']] = session
