from datetime import datetime
import json
import time
import threading
import bluetooth._bluetooth as bluez

from . import blescan
from .. import socketio
from .config import tilt_active_sessions_path
from .model import TiltSession
from .session_parser import active_tilt_sessions

TILTS = {
    'a495bb10c5b14b44b5121370f02d74de': 'Red',
    'a495bb20c5b14b44b5121370f02d74de': 'Green',
    'a495bb30c5b14b44b5121370f02d74de': 'Black',
    'a495bb40c5b14b44b5121370f02d74de': 'Purple',
    'a495bb50c5b14b44b5121370f02d74de': 'Orange',
    'a495bb60c5b14b44b5121370f02d74de': 'Blue',
    'a495bb70c5b14b44b5121370f02d74de': 'Yellow',
    'a495bb80c5b14b44b5121370f02d74de': 'Pink',
}

_lock = None
_socket = None

def run(app):
    dev_id = 0
    global _lock
    global _socket
    try:
        _lock = threading.Lock()
        _socket = bluez.hci_open_dev(dev_id)
        print ("Starting Tilt collection thread")
    except:
        print ("Error accessing bluetooth device. Shutting down Tilt thread...")
        return

    blescan.hci_le_set_scan_parameters(_socket)
    blescan.hci_enable_le_scan(_socket)
    monitor_tilt(app)

def monitor_tilt(app):
    global _socket
    while True:
        beacons = distinct(blescan.parse_events(_socket, 10))
        with app.app_context():
            for beacon in beacons:
                if beacon['uuid'] in TILTS.keys():
                        # maintain same field names as pytilt in case someone wants to use that
                        process_tilt_data({
                            'color': TILTS[beacon['uuid']],
                            'timestamp': datetime.now().isoformat(),
                            'temp': beacon['major'], # fahrenheit
                            'gravity': beacon['minor']
                        })
        # TODO: make time configurable
        time.sleep(10)

# this can also be called from routes_tilt_api.py if the user is running an external pytilt service
def process_tilt_data(data):
    global _lock
    with _lock:
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
                'temp': data['temp'],
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


def distinct(objects):
    seen = set()
    unique = []
    for obj in objects:
        if obj['uuid'] not in seen:
            unique.append(obj)
            seen.add(obj['uuid'])
    return unique

def create_new_session(uid):
    if uid not in active_tilt_sessions:
        active_tilt_sessions[uid] = TiltSession()
    active_tilt_sessions[uid].uninit = False
    active_tilt_sessions[uid].start_time = datetime.now()  # Not now, but X samples * 60*RATE sec ago
    active_tilt_sessions[uid].filepath = tilt_active_sessions_path().joinpath('{0}#{1}.json'.format(active_tilt_sessions[uid].start_time.strftime('%Y%m%d_%H%M%S'), uid))
    active_tilt_sessions[uid].file = open(active_tilt_sessions[uid].filepath, 'w')
    active_tilt_sessions[uid].file.write('[')
