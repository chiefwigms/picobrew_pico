import json
import os
import uuid
from datetime import datetime, timedelta
from flask import current_app
from webargs import fields
from webargs.flaskparser import use_args, FlaskParser

from .. import socketio
from . import main
from .config import MachineType, kegsmarts_active_sessions_path
from .firmware import firmware_upgrade_required
from .model import KegSmartsSession, KegSmartsKegSession, KegSmartsSensor, KegSmartSensorType, KegSmartSensorState
from .routes_frontend import get_pico_recipes, get_zymatic_recipes, get_zseries_recipes
from .session_parser import active_kegsmarts_sessions, active_kegsmarts_keg_sessions, get_archived_sessions, ZSessionType, epoch_millis_converter


arg_parser = FlaskParser()


# Notification: /api/ks/notification?machine={UID}&firm={Version}
#     Response: '#{0}#\r\n' where {0} : Alert:<message to display>
register_args = {
    'machine': fields.Str(required=True),       # 32 character alpha-numeric serial number
    'firm': fields.Str(required=False),         # semantic versioned firmware version (latest: 1.0.6)
}


@main.route('/api/ks/notification')
@use_args(register_args, location='querystring')
def process_notification(args):
    firmware_version = args.get('firm', "")
    if firmware_upgrade_required(MachineType.KEGSMARTS, firmware_version):
        return '#Alert: New firmware available on picobrew.com#\r\n'
    return '##\r\n'


# Configure: /api/ks/rev1/configure?machine={UID}&sensors={SENSOR_DATA}&mintemp={MIN_TEMP}&tempData={TEMP}
#  Response: '##\r\n'
configure_args = {
    'machine':  fields.Str(required=True),   # 32 character alpha-numeric serial number
    'sensors':  fields.Str(required=True),   # array of strings encoded as "{Location}_{UID}_{Type}(_{ID})" separated by "!" example: "sensors=0_bb60caa11603_0!3_123ac7190000_1_1!0_123bc7190000_1_2!3_aa1cbe931604_2_1"
    'mintemp':  fields.Str(required=True),   # Temperature in Fahrenheit, appears to always be "32" (freezing).
    'tempData': fields.Str(required=True),   # Temperature in Fahrenheit, the current user-selected temperature
}


@main.route('/api/ks/rev1/configure')
@use_args(configure_args, location='querystring')
def process_configure_request(args):
    uid = args['machine']
    
    if uid not in active_kegsmarts_sessions:
        active_kegsmarts_sessions[uid] = KegSmartsSession()
        active_kegsmarts_sessions[uid].uid = uid
        active_kegsmarts_sessions[uid].minTemp = args['mintemp']
        active_kegsmarts_sessions[uid].tempData = args['tempData']
    
    if uid not in active_kegsmarts_keg_sessions:
        active_kegsmarts_keg_sessions[uid] = {}
    
    active_keg_sessions = active_kegsmarts_keg_sessions[uid]
    # if uid not in active_kegsmart_sessions or active_kegsmart_sessions[uid].name == 'Waiting To Keg':
    #     create_new_session(uid, None, None)

    # example 0_bb60caa11603_0!3_123ac7190000_1_1!0_123bc7190000_1_2!3_aa1cbe931604_2_1
    sensors = args['sensors'].split("!")
    for i in range(len(sensors)):
        sensor_data = sensors[i].split('_')
        ks_sensor = KegSmartsSensor()
        ks_sensor.location = int(sensor_data[0])
        ks_sensor.guid = sensor_data[1]
        ks_sensor.type = KegSmartSensorType(int(sensor_data[2]))
        if len(sensor_data) > 3:
            ks_sensor.id = int(sensor_data[3])
            ks_sensor.alias = f'{ks_sensor.type} {ks_sensor.id}'

        if ks_sensor.location != 0:
            if ks_sensor.location not in active_keg_sessions:
                active_session = KegSmartsKegSession()
                active_session.uid = uid
                active_session.location = ks_sensor.location
                active_session.sensors = {}
                active_session.sensors[ks_sensor.guid] = ks_sensor
                active_keg_sessions[ks_sensor.location] = active_session
            else:
                active_session = active_keg_sessions[ks_sensor.location]
                if ks_sensor.guid not in active_session.sensors:
                    active_session.sensors[ks_sensor.guid] = ks_sensor
            
            # add reference to sensor to kegsmarts session
            if ks_sensor.guid not in active_kegsmarts_sessions[uid].sensors:
                active_kegsmarts_sessions[uid].sensors[ks_sensor.guid] = ks_sensor

    return '##\r\n'


#      Log: /api/ks/rev1/log?machine={UID}&data={DATA}
# Response: '#{0}#\r\n' where {0} : 0 = Periodic Logging, 1 = Fetch State Required (user initiated changes, device rebooted)
log_args = {
    'machine': fields.Str(required=True),        # 32 character alpha-numeric serial number
    'data':    fields.Str(required=True),        # array of data points (first data point is always thermometer)
}


@main.route('/api/ks/rev1/log')
@use_args(log_args, location='querystring')
def process_log_request(args):
    uid = args['machine']
    # if uid not in active_kegsmart_sessions or active_kegsmart_sessions[uid].name == 'Waiting To Keg':
    #     create_new_session(uid, None, None)
    
    active_kegsmarts_session = active_kegsmarts_sessions[uid]
    active_keg_sessions = active_kegsmarts_keg_sessions[uid]

    # parse session {DATA} element
    data = args['data']
    sensors_data = data.split('!')

    for i in range(len(sensors_data)):
        sensor_data = sensors_data[i].split('_')
        if len(sensor_data) < 5: 
            break  # query string ends with '!' for an odd reason
        
        current_app.logger.debug(f'parse sensor data {sensor_data}')
        location = int(sensor_data[0])
        temperature = int(sensor_data[1])
        
        if location == 0:   # thermometer data format "0_{T}_0_0_0" where {T} is current temperature in Fahrenheit
            for i in active_keg_sessions: active_keg_sessions[i].fridge_temp = temperature
        else:               # keg sensor data format "{Location}_{kT}_{kOz}_{State}_{Weight}(_Fermentation_{n}_{Time}_{fT})"
            current_app.logger.debug(f'fetch keg location {location} from kegs {(active_keg_sessions)}')
            keg_session = active_keg_sessions.get(location)
            session_data = {
                'time': ((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000),
                'fridge_temp': keg_session.fridge_temp,
                'temp': temperature,
                'volume': int(sensor_data[2]),  # oz
                'weight': int(sensor_data[4]),  # grams (liquid only = total - keg tare weight)
                'state': KegSmartSensorState(int(sensor_data[3])),
            }

            if session_data['state'] == KegSmartSensorState.FERMENTING:
                session_data.update({
                    "fermenting_location": f'{sensor_data[5]}_{sensor_data[6]}',
                    "time_remaining": int(sensor_data[7]),
                    "goal_temp": int(sensor_data[8]),
                })
            
            keg_session.data.append(session_data)
            graph_update = json.dumps({
                'time': session_data['time'],
                'data': [session_data['fridge_temp'], session_data['temp'], session_data['weight']],
                'location': location,
                'state': session_data['state'],
            })
            socketio.emit('kegsmarts_session_update|{}'.format(uid), graph_update)

    if len(active_kegsmarts_session.metadata) == 0:
        return '#1#\r\n'  # fetch keg/tap metadata
    else:
        return '#0#\r\n'


# Fetch KegSmart State: /api/ks/rev1/ksget?machine={UID}
#             Response: '#{NAME}|{TT}|{kT}|${D}${K}$#\r\n' 
#                   where {NAME} : name; 
#                         {TT} : total taps;
#                         {kT} : goal temp;
#                         {D} (array) : device sensor info "{Type}|{Location}|{ID}"; 
#                         {K} (array) : keg display data in two formats
#                             on tap / on deck : "{Type}|{Location}|{ABV}|{IBU}|{Temp}|{user}|{Beer Name}|{Beer Style}|{Hops}|{Grains}|{Rating}|{DaysT}|{kWeight}|{Oz Remaining}"
#                             fermenting : "{Type}|{Location}|{Beer Name}|{hash}|{fT}|{fState}|{Time}|{Ferment}|{Crash"
kegsmart_state_args = {
    'machine': fields.Str(required=True),       # 32 character alpha-numeric serial number
}


@main.route('/api/ks/rev1/ksget')
@use_args(kegsmart_state_args, location='querystring')
def process_kegsmart_state_request(args):
    uid = args['machine']

    active_kegsmarts_session = active_kegsmarts_sessions[uid]
    active_keg_sessions = active_kegsmarts_keg_sessions[uid]

    alias = active_kegsmarts_session.alias
    num_taps = len(active_kegsmarts_session.kegs) - 1  # last keg is reserved for fermentation
    target_temp = 50
    kegsmart_state = f'{alias}|{num_taps}|{target_temp}'

    sensor_data = ''
    for sId in active_kegsmarts_session.sensors:
        sensor = active_kegsmarts_session.sensors[sId]
        # not sure why configure and ksget use different encoding for sensor/device type
        device_type = 4 if sensor.type == KegSmartSensorType.KEG_PLATE else 5 if sensor.type == KegSmartSensorType.KEG_WARMER else None
        sensor_data += f'${device_type}|{sensor.location}|{sensor.id}'
    
    keg_data = ''
    for kId in active_keg_sessions:
        keg = active_keg_sessions[kId]
        keg_data += f'${keg.type}|{keg.location}'

        if keg.type == 1:    #     on tap => "|ABV|IBU|Temp|user|Beer Name|Beer Style|Hops|Grains|Rating|DaysT|kWeight|Oz Remaining"
            tapped_at = epoch_millis_converter(keg.tapped_at)
            duration_days = round((datetime.utcnow() - tapped_at) / timedelta(days=1), 2)
            keg_data += f'|7.2|70|{active_kegsmarts_session.temp}|picobrew_pico|<>|<>|<>|<>|<>|{duration_days}|{keg.weight}|{keg.volume}'
        elif keg.type == 2:  # fermenting => "|Beer Name|hash|fT|fState|Time|Ferment|Crash"
            ferment_start = epoch_millis_converter(keg.ferment_start)
            ferment_duration = round((datetime.utcnow() - ferment_start) / timedelta(mins=1), 2)
            recipe = recipe_by_name(keg.session)
            keg_data += f'{recipe.name}|{keg.session}|68|{keg.state}|{ferment_duration}|Fermentation,68,14400|Crash Chill,38,0<>'
        else:                # inactive
            keg_data += f'${keg.type}|{kId}'

    #|-1|50$1|1|1$1|2|2$2|3|1$0|1$0|2$0|3#
    return f'#{kegsmart_state}{sensor_data}{keg_data}#\r\n'


# Acknowledge KegSmart State: /api/ks/rev1/ksacknowledge?machine={UID}
#             Response: '#{N}#\r\n' where {N} : 0
kegsmart_acknowledge_state_args = {
    'machine': fields.Str(required=True),       # 32 character alpha-numeric serial number
}


@main.route('/api/ks/rev1/ksacknowledge')
@use_args(kegsmart_acknowledge_state_args, location='querystring')
def process_kegsmart_acknowledge_request(args):
    # simply is a request that acknowledges receipt of the former ksget request
    return '#0#\r\n'


#  Ferment: /api/ks/rev1/ferment?machine={UID}&code={CODE}&session={SESSION}&tap={TAP}
# Response: 
#           code=0 : '#{FERM_SESSION_1}|{FERM_SESSION_2}...#\r\n' 
#                    where {FERM_SESSION_1/2} : available sessions for fermentation (*Beer Name == already fermented and ordered to end of list)
#
#           code=1 : '#{fSTEP}/{fT}/{TIME}/Crash Chill/{cT}/{cTIME}#\r\n' 
#                    where {fSTEP} : fermentation step name ;
#                             {fT} : goal temp for fermentation step ;
#                          {fTIME} : remaining in fermentation step ; 
#                             {cT} : goal temp for crash
#                          {cTIME} : seems to always be 0 for cold crash step
#
#           code=3 : '##\r\n' 
ferment_request_args = {
    'machine': fields.Str(required=True),       # 32 character alpha-numeric serial number
    'code':    fields.Int(required=True),       # 0 = Pull List From Server, 1 = Pull Session Info, 3 = Cold Crash
    'session': fields.Str(required=False),      # (optional) session uid (from code=0 request response)
    'tap':     fields.Int(required=False),      # (optional) number 1,2,3, or 4 : 2-tap -> tap 1-2, keg 3 ; 3-tap -> tap 1-3, keg 4
    'ferment': fields.Int(required=False),      # (optional) number 1,2,3, or 4 : 2-tap -> tap 1-2, keg 3 ; 3-tap -> tap 1-3, keg 4
}


@main.route('/api/ks/rev1/ferment')
@use_args(ferment_request_args, location='querystring')
def process_ferment_request(args):
    brew_sessions = get_archived_sessions()

    code = args['code']

    if code == 0:        # list fermentable and on deck beer sessions
        brewed_beer = ""

        # TODO - filter brew sessions by fermented or not (presence of kegsmart session);
        for session in brew_sessions:
            name = session['name']
            sid = session['session']
            
            # filter to only beer sessions
            if (session['type'] == ZSessionType.BEER.value or name.upper() not in ["RINSE", "CLEAN", "DEEP CLEAN", "RACK", "DRAIN"]):
                if len(brewed_beer) != 0:
                    brewed_beer += "|"
                brewed_beer += f'{name}/{sid}'

        return f'#{brewed_beer}#\r\n'
    
    elif code == 1:     # pull specific fermentation step information
        sid = args['session']
        session = next((s for s in brew_sessions if s['session'] == sid), None)
        if session != None:
            current_app.logger.debug(f'found {session["name"]} for selected session {sid}')
            recipe = recipe_by_name(session['name'])
            
            if recipe != None:
                current_app.logger.debug(f'found {recipe.name} for selected session {sid}')
                # TODO: recipes need to include fermentation steps...
                # return specific recipe fermentation steps
                # Fermentation/fT/Time|Crash Chill/cT/0#
            
        current_app.logger.warn(f'failed to find recipe {session["name"]} fermentation steps - returning default ale fermentation for session {sid}')
        # Fermentation/fT/Time|Crash Chill/cT/0#
        return '#Fermentation/68/14400|Crash Chill/38/0#\r\t'

    elif code == 3:     # cold crash
        return '##\r\t'


#  Rate Beer: /api/ks/ratebeer?machine={UID}&tap={TAP}&rating={rating
#   Response: '##\r\n' 
ferment_request_args = {
    'machine': fields.Str(required=True),       # 32 character alpha-numeric serial number
    'tap':     fields.Int(required=True),       # 1-3 based on taps available
    'rating':  fields.Int(required=True),       # 0-10 (converts to 0.0 - 5.0 stars with 0.5 values supported)
}


@main.route('/api/ks/ratebeer')
@use_args(ferment_request_args, location='querystring')
def process_ratebeer_request(args):
    # TODO - not supported at this time (would likely end up adding ratings into the recipe's JSON file structure)
    return '##\r\t'

# -------- Utility --------
def recipe_by_name(name):
    recipe = next((r for r in get_pico_recipes() if r.name == name), None)
    if recipe == None:
        recipe = next((r for r in get_zymatic_recipes() if r.name == name), None)
    if recipe == None:
        recipe = next((r for r in get_zseries_recipes() if r.name == name), None)
    
    return recipe

def create_new_session(uid, location, sesId, name):
    if uid not in active_kegsmarts_sessions:
        active_kegsmarts_sessions[uid] = {}
    
    active_sessions = active_kegsmarts_sessions[uid]
    if location not in active_sessions:
        active_sessions[location] = KegSmartsSession()

    # replace spaces and '#' with other character sequences
    filename = '{0}#{1}#{2}#{3}#{4}.json'.format(datetime.now().strftime('%Y%m%d_%H%M%S'), uid, location, sesId, name)
    active_kegsmarts_sessions[uid].filepath = kegsmarts_active_sessions_path().joinpath(filename)
    active_kegsmarts_sessions[uid].file = open(active_kegsmarts_sessions[uid].filepath, 'w')
    active_kegsmarts_sessions[uid].file.write('[')


def cleanup_old_session(uid):
    if uid in active_kegsmarts_sessions and active_kegsmarts_sessions[uid].file:
        active_kegsmarts_sessions[uid].file.seek(0, os.SEEK_END)
        active_kegsmarts_sessions[uid].file.seek(active_kegsmarts_sessions[uid].file.tell() - 1, os.SEEK_SET)  # Remove trailing , from last data set
        active_kegsmarts_sessions[uid].file.write('\n]\n')
        active_kegsmarts_sessions[uid].cleanup()
