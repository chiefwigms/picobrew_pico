import json
from datetime import datetime
from webargs import fields
from webargs.flaskparser import use_args, FlaskParser

from . import main
from .. import socketio
from .config import ferm_active_sessions_path
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
    return '#0#'


# Get State: /API/PicoFerm/getState?uid={UID}
#  Response: '#{0}#' where {0} : 2,4 = nothing to do, 10,0 = in progress/send data, 10,16 = in progress/error, 2,16 = complete/stop sending data
get_ferm_state_args = {
    'uid': fields.Str(required=True),   # 12 character alpha-numeric serial number
}
@main.route('/API/PicoFerm/getState')
@use_args(get_ferm_state_args, location='querystring')
def process_get_ferm_state(args):
    if args['uid'] not in active_ferm_sessions:
        create_new_session(args['uid'])
    # TODO - Define logic on state - for now request information from PicoFerm
    return '#10,0#'


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
        log_data += '\t{},\n'.format(json.dumps(point))
    active_ferm_sessions[uid].data.extend(session_data)
    active_ferm_sessions[uid].voltage = str(args['voltage']) + 'V'
    graph_update = json.dumps({'voltage': args['voltage'], 'data': session_data})
    socketio.emit('ferm_session_update|{}'.format(args['uid']), graph_update)
    if (datetime.now().date() - active_ferm_sessions[uid].start_time.date()).days > 14:
        active_ferm_sessions[uid].file.write('{}\n]'.format(log_data[:-2]))
        active_ferm_sessions[uid].cleanup()
        return '#2,4#'
    else:
        active_ferm_sessions[uid].file.write(log_data)
        active_ferm_sessions[uid].file.flush()
        return '#10,0#'  # Errors like '10,16' send data but mark data error.  '10,0' tells the PicoFerm to continue to send data.  The server makes a determination when fermenting is done based on the datalog after it sends '2,4'


# -------- Utility --------
def create_new_session(uid):
    if uid not in active_ferm_sessions:
        active_ferm_sessions[uid] = PicoFermSession()
    active_ferm_sessions[uid].uninit = False
    active_ferm_sessions[uid].start_time = datetime.now()  # Not now, but X samples * 60*RATE sec ago
    active_ferm_sessions[uid].filepath = ferm_active_sessions_path().joinpath('{0}#{1}.json'.format(active_ferm_sessions[uid].start_time.strftime('%Y%m%d_%H%M%S'), uid))
    active_ferm_sessions[uid].file = open(active_ferm_sessions[uid].filepath, 'w')
    active_ferm_sessions[uid].file.write('[\n')
