from webargs import fields
from webargs.flaskparser import use_args, FlaskParser
from marshmallow import INCLUDE, Schema
import threading
from datetime import datetime
import json

from . import main
from .units import convert_temp
from .. import socketio
from .config import tilt_active_sessions_path
from .model import TiltSession
from .session_parser import active_tilt_sessions

_lock = threading.Lock()
arg_parser = FlaskParser()


# This supports using pytilt to get the data from the tilt using bluetooth and send via this API call
# See https://github.com/atlefren/pytilt but all you have to do is set the environment variable
#   PYTILT_URL=<your picobrew_pico server>/API/tilt
# and it will work without modifications
class TiltSchema(Schema):
    color = fields.Str(required=True),      # device ID
    temp = fields.Float(required=True),     # device temperature in Celcius
    gravity = fields.Int(required=True),    # calculated specific gravity
    timestamp = fields.Str(required=True),  # time sample taken in ISO format e.g '2021-03-06T16:25:42.823122'


# Process tilt Data: /API/tilt
@main.route('/API/tilt', methods=['POST'])
@use_args(TiltSchema(many=True), unknown=INCLUDE)
def process_tilt_dataset(dataset):
    for data in dataset:
        data['temp'] = convert_temp(data['temp'], 'F')
        process_tilt_data(data)
    return('', 200)


# this can also be called from tilt.py and when using bluetooth, more data is available
# including a uid and rssi (signal strength)
def process_tilt_data(data):
    global _lock
    with _lock:
        # pytilt will just have color, but the bluetooth data from tilt.py will have uid as well
        # so we favor that
        uid = data['uid'] if 'uid' in data else data['color']

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
                'temp': data['temp'],
                'gravity': data['gravity'] / 1000,
                'rssi': data['rssi'],
            }

            session_data.append(point)
            log_data += '\n\t{},'.format(json.dumps(point))

            active_tilt_sessions[uid].data.extend(session_data)
            active_tilt_sessions[uid].rssi = str(data['rssi'])
            graph_update = json.dumps({'rssi': data['rssi'], 'data': session_data})
            socketio.emit('tilt_session_update|{}'.format(uid), graph_update)

            # end fermentation only when user specifies fermentation is complete
            if (active_tilt_sessions[uid].uninit is False and active_tilt_sessions[uid].active is False):
                active_tilt_sessions[uid].file.write('{}\n\n]'.format(log_data[:-2]))
                active_tilt_sessions[uid].cleanup()
            else:
                active_tilt_sessions[uid].active = True
                active_tilt_sessions[uid].file.write(log_data)
                active_tilt_sessions[uid].file.flush()


def create_new_session(uid):
    if uid not in active_tilt_sessions:
        active_tilt_sessions[uid] = TiltSession()
    active_tilt_sessions[uid].uninit = False
    active_tilt_sessions[uid].start_time = datetime.now()

    date_time_str = active_tilt_sessions[uid].start_time.strftime('%Y%m%d_%H%M%S')
    filepath = tilt_active_sessions_path().joinpath('{0}#{1}.json'.format(date_time_str, uid))

    active_tilt_sessions[uid].filepath = filepath
    active_tilt_sessions[uid].file = open(active_tilt_sessions[uid].filepath, 'w')
    active_tilt_sessions[uid].file.write('[')
