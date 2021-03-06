import json
from datetime import datetime
from webargs import fields
from webargs.flaskparser import use_args, FlaskParser
from flask import request
from marshmallow import INCLUDE, Schema

from . import main
from .. import socketio
from .config import tilt_active_sessions_path
from .model import TiltSession
from .session_parser import active_tilt_sessions
from .units import convert_temp


arg_parser = FlaskParser()

# This is based on using pytilt to get the data from the tilt using bluetooth and send via this API call
# See https://github.com/atlefren/pytilt but all you have to do is set the environment variable
#   PYTILT_URL=<your picobrew_pico server>/API/tilt
# and it will work without modifications
# TODO: look to integrate this into picobrew_pico using an nginx Timer or something.

class TiltSchema(Schema):
    color = fields.Str(required=True),     # device ID
    temp = fields.Float(required=True),    # device temperature
    gravity = fields.Int(required=True),   # calculated specific gravity
    timestamp = fields.Str(required=True), # time sample taken in ISO format e.g '2021-03-06T16:25:42.823122'

# Process tilt Data: /API/tilt
@main.route('/API/tilt', methods=['POST'])
@use_args(TiltSchema(many=True), unknown=INCLUDE)
def process_tilt_dataset(dataset):
    for data in dataset:
        process_tilt_data(data)
    return('', 200)

def process_tilt_data(data):
    uid = data['color']
    
    if uid not in active_tilt_sessions:
        active_tilt_sessions[uid] = TiltSession()

    if active_tilt_sessions[uid].active:
        # initialize session and session files
        if active_tilt_sessions[uid].uninit:
            create_new_session(uid)

        time = (datetime.fromisoformat(data['timestamp']) - datetime(1970, 1, 1)).total_seconds() * 1000
        session_data = []
        log_data = ''
        point = {
            'time': time,
            'temp': convert_temp(data['temp'], 'F'),
            'gravity': (data['gravity'] / 1000) if data['gravity'] > 1000 else data['gravity'],
        }

        session_data.append(point)
        log_data += '\n\t{},'.format(json.dumps(point))
        
        active_tilt_sessions[uid].data.extend(session_data)
        graph_update = json.dumps({'voltage': None, 'data': session_data})
        socketio.emit('tilt_session_update|{}'.format(uid), graph_update)
        
        # end fermentation only when user specifies fermentation is complete
        if (active_tilt_sessions[uid].uninit == False and active_tilt_sessions[uid].active == False):
            active_tilt_sessions[uid].file.write('{}\n\n]'.format(log_data[:-2]))
            active_tilt_sessions[uid].cleanup()
        else:
            active_tilt_sessions[uid].active = True
            active_tilt_sessions[uid].file.write(log_data)
            active_tilt_sessions[uid].file.flush()

# -------- Utility --------
def create_new_session(uid):
    if uid not in active_tilt_sessions:
        active_tilt_sessions[uid] = TiltSession()
    active_tilt_sessions[uid].uninit = False
    active_tilt_sessions[uid].start_time = datetime.now()  # Not now, but X samples * 60*RATE sec ago
    active_tilt_sessions[uid].filepath = tilt_active_sessions_path().joinpath('{0}#{1}.json'.format(active_tilt_sessions[uid].start_time.strftime('%Y%m%d_%H%M%S'), uid))
    active_tilt_sessions[uid].file = open(active_tilt_sessions[uid].filepath, 'w')
    active_tilt_sessions[uid].file.write('[')
