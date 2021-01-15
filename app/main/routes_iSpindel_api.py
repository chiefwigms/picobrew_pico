import json
from datetime import datetime
from webargs import fields
from webargs.flaskparser import use_args, FlaskParser
from flask import request

from . import main
from .. import socketio
from .config import iSpindel_active_sessions_path
from .model import iSpindelSession
from .session_parser import active_iSpindel_sessions

arg_parser = FlaskParser()

iSpindel_dataset_args = {
    'name': fields.Str(required=True),           #device name
    'ID' : fields.Int(required=True),            #random device ID
    'angle' : fields.Float(required=True),       #device floatation angle
    'temperature' : fields.Float(required=True), #device temperature
    'temp_units' : fields.Str(required=True),    #temperature units in C or F
    'battery' : fields.Float(required=True),     #device battery voltage
    'gravity' : fields.Float(required=True),     #calculated specific gravity
    'interval' : fields.Int(required=True),      #sampling interval in seconds
    'RSSI' : fields.Int(required=True)           #RSSI of WiFi signal
}

# Process iSpindel Data: /API/iSpindel
@main.route('/API/iSpindel', methods=['POST'])
def process_iSpindel_data():
    data = request.get_json()
    uid = str(data['ID'])
    
    if uid not in active_iSpindel_sessions or active_iSpindel_sessions[uid].uninit:
        create_new_session(uid)

    time = ((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)
    session_data = []
    log_data = ''
    point = {
        'time': time,
        'temp': data['temperature'],
        'gravity': data['gravity'],
    }

    session_data.append(point)
    log_data += '\t{},\n'.format(json.dumps(point))
    
    active_iSpindel_sessions[uid].data.extend(session_data)
    active_iSpindel_sessions[uid].voltage = str(data['battery']) + 'V'
    
    graph_update = json.dumps({'voltage': data['battery'], 'data': session_data})
    socketio.emit('iSpindel_session_update|{}'.format(data['ID']), graph_update)
    
    if (datetime.now().date() - active_iSpindel_sessions[uid].start_time.date()).days > 14:
        active_iSpindel_sessions[uid].file.write('{}\n]\n'.format(log_data[:-2]))
        active_iSpindel_sessions[uid].cleanup()
        return ('', 200)
    else:
        active_iSpindel_sessions[uid].file.write(log_data)
        active_iSpindel_sessions[uid].file.flush()
        return ('', 200)  
    
# -------- Utility --------
def create_new_session(uid):
    if uid not in active_iSpindel_sessions:
        active_iSpindel_sessions[uid] = iSpindelSession()
    active_iSpindel_sessions[uid].uninit = False
    active_iSpindel_sessions[uid].start_time = datetime.now()  # Not now, but X samples * 60*RATE sec ago
    active_iSpindel_sessions[uid].filepath = iSpindel_active_sessions_path().joinpath('{0}#{1}.json'.format(active_iSpindel_sessions[uid].start_time.strftime('%Y%m%d_%H%M%S'), uid))
    active_iSpindel_sessions[uid].file = open(active_iSpindel_sessions[uid].filepath, 'w')
    active_iSpindel_sessions[uid].file.write('[\n')
