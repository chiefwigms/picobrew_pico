import json
from datetime import datetime
from flask import current_app, send_from_directory
from webargs import fields
from webargs.flaskparser import use_args, FlaskParser

from . import main
from .. import socketio
from .config import ferm_active_sessions_path, picoferm_firmware_path, MachineType
from .firmware import firmware_filename, minimum_firmware, firmware_upgrade_required
from .model import PicoFermSession
from .session_parser import active_ferm_sessions

arg_parser = FlaskParser()


# Register: /API/PicoFerm/isRegistered?uid={uid}&token={token}
# Response: '#{0}#' where {0} : 1 = Registered, 0 = Not Registered
ferm_registered_args = {
    'uid': fields.Str(required=True),       # 12 character alpha-numeric serial number
    'token': fields.Str(required=True),    # 8 character alpha-numberic number
}
@main.route('/API/PicoFerm/isRegistered')
@use_args(ferm_registered_args, location='querystring')
def process_ferm_registered(args):
    uid = args['uid']
    if uid not in active_ferm_sessions:
        active_ferm_sessions[uid] = PicoFermSession()
    return '#1#'


# Check Firmware: /API/PicoFerm/checkFirmware?uid={UID}&version={VERSION}
#           Response: '#{0}#' where {0} : 1 = Update Available, 0 = No Updates
check_ferm_firmware_args = {
    'uid': fields.Str(required=True),       # 12 character alpha-numeric serial number
    'version': fields.Str(required=True),   # Current firmware version - i.e. 0.1.11
}
@main.route('/API/PicoFerm/checkFirmware')
@use_args(check_ferm_firmware_args, location='querystring')
def process_check_ferm_firmware(args):
    if firmware_upgrade_required(MachineType.PICOFERM, args['version']):
        return '#1#'
    return '#0#'


# Get Firmware: /API/pico/getFirmware?uid={UID}
#     Response: RAW Bin File Contents
get_firmware_args = {
    'uid': fields.Str(required=True),       # 12 character alpha-numeric serial number
}
@main.route('/API/PicoFerm/getFirmwareAddress')
@use_args(get_firmware_args, location='querystring')
def process_get_firmware_address(args):
    filename = firmware_filename(MachineType.PICOFERM, minimum_firmware(MachineType.PICOFERM))
    return '#http://picobrew.com/firmware/picoferm/{}#'.format(filename)


# Get Firmware: /firmware/picoferm/<version>
#     Response: RAW Bin File
@main.route('/firmware/picoferm/<file>', methods=['GET'])
def process_picoferm_firmware(file):
    current_app.logger.debug('DEBUG: PicoFerm fetch firmware file={}'.format(file))
    return send_from_directory(picoferm_firmware_path(), file)


# Get State: /API/PicoFerm/getState?uid={UID}
#  Response: '#{0}#' where {0} : 2,4 = nothing to do, 10,0 = in progress/send data, 10,16 = in progress/error, 2,16 = complete/stop sending data
get_ferm_state_args = {
    'uid': fields.Str(required=True),   # 12 character alpha-numeric serial number
}
@main.route('/API/PicoFerm/getState')
@use_args(get_ferm_state_args, location='querystring')
def process_get_ferm_state(args):
    uid = args['uid']
    if uid not in active_ferm_sessions:
        active_ferm_sessions[uid] = PicoFermSession()
    
    session = active_ferm_sessions[uid]

    if session.active == True:
        return '#10,0#'
    elif session.uninit or session.file == None:
        return '#2,4'


# LogDataSet: /API/PicoFerm/logDataSet?uid={UID}&rate={RATE}&voltage={VOLTAGE}&data={DATA}
#   Response: '#{0}#' where {0} : 10,0 = in progress/send data, ?????
log_ferm_dataset_args = {
    'uid': fields.Str(required=True),        # 12 character alpha-numeric serial number
    'rate': fields.Float(required=True),     # Rate between samples (minutes)
    'voltage': fields.Float(required=True),  # %0.2f Voltage
    'data': fields.Str(required=True),       # List of dictionary (Temperature (S1), Pressure (S2)): [{"s1":%0.2f,"s2":%0.2f},]
}
@main.route('/API/PicoFerm/logDataSet')
@use_args(log_ferm_dataset_args, location='querystring')
def process_log_ferm_dataset(args):
    uid = args['uid']

    if uid not in active_ferm_sessions or active_ferm_sessions[uid].uninit:
        create_new_session(uid)

    data = json.loads(args['data'])
    time_delta = args['rate'] * 60 * 1000
    time = ((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000) - (time_delta * (len(data) - 1))

    session_data = []
    log_data = ''
    for d in data:
        point = {'time': time,
                 'temp': d['s1'],
                 'pres': d['s2'],
                 }
        session_data.append(point)
        time = time + time_delta
        log_data += '\n\t{},'.format(json.dumps(point))

    active_ferm_sessions[uid].data.extend(session_data)
    active_ferm_sessions[uid].voltage = str(args['voltage']) + 'V'
    graph_update = json.dumps({'voltage': args['voltage'], 'data': session_data})
    socketio.emit('ferm_session_update|{}'.format(args['uid']), graph_update)


    # end fermentation only when user specifies fermentation is complete
    if active_ferm_sessions[uid].uninit == False and active_ferm_sessions[uid].active == False:
        active_ferm_sessions[uid].file.write('{}\n\n]'.format(log_data[:-2]))
        active_ferm_sessions[uid].cleanup()
        # The server makes a determination when fermenting is done based on the datalog after it sends '2,4'
        return '#2,4#'
    else:
        active_ferm_sessions[uid].active = True
        active_ferm_sessions[uid].file.write(log_data)
        active_ferm_sessions[uid].file.flush()
        # Errors like '10,16' send data but mark data error.
        # '10,0' tells the PicoFerm to continue to send data.
        return '#10,0#'


# -------- Utility --------
def create_new_session(uid):
    if uid not in active_ferm_sessions:
        active_ferm_sessions[uid] = PicoFermSession()
    active_ferm_sessions[uid].uninit = False
    active_ferm_sessions[uid].start_time = datetime.now()  # Not now, but X interval seconds ago
    active_ferm_sessions[uid].filepath = ferm_active_sessions_path().joinpath('{0}#{1}.json'.format(active_ferm_sessions[uid].start_time.strftime('%Y%m%d_%H%M%S'), uid))
    active_ferm_sessions[uid].file = open(active_ferm_sessions[uid].filepath, 'w')
    active_ferm_sessions[uid].file.write('[')
