# Function(s) to initiate a new PicoStill session and poll
# the device's data URI to build a local distillation session
import json
import requests

from . import main
from .. import socketio
from flask import current_app
from .config import still_active_sessions_path, still_archive_sessions_path
from .model import PicoStillSession
from .session_parser import active_still_sessions

from time import sleep
from datetime import datetime
from threading import Thread

class FlaskThread(Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = current_app._get_current_object()
    
    def run(self):
      with self.app.app_context():
        super().run()


def poll_still(still_ip, uid):
    datastring = None
    try:
        # Attempt to connect to the PicoStill data feed
        still_data_uri = 'http://{}/data'.format(still_ip)
        current_app.logger.debug('DEBUG: Retrieve PicoStill Data - {}'.format(still_data_uri))
        r = requests.get(still_data_uri)
        datastring = r.text.strip()
        current_app.logger.debug('DEBUG: Still Datastring: {}'.format(datastring))
    except:
      return False

    if not datastring or datastring[0] != '#':
      return False
     
    datastring = datastring[1:-1]
    t1,t2,t3,t4,pres,ok,d1,d2,errmsg = datastring.split(',')
    time = (datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000
    session_data = []
    log_data = ''
    point = {'time': time,
             't1': t1,
             't2': t2,
             't3': t3,
             't4': t4,
             'pres': pres,
             }
    session_data.append(point)
    log_data += '\t{},\n'.format(json.dumps(point))

    active_still_sessions[uid].data.extend(session_data)
    graph_update = json.dumps({'data': session_data})
    socketio.emit('still_session_update|{}'.format(uid), graph_update)

    active_still_sessions[uid].file.write(log_data)
    active_still_sessions[uid].file.flush()

    return (ok, errmsg)

def new_still_session(still_ip, device_id):
    global connection_failures

    connection_failures = 0
    uid = device_id
    if uid not in active_still_sessions or active_still_sessions[uid].uninit:
        create_new_session(uid)
    else:
        # If we have an old session, clean it up and create a new one...
        active_still_sessions[uid].file.write('\n]')
        active_still_sessions[uid].cleanup()
        create_new_session(uid)

    while connection_failures < 3:
        result = poll_still(still_ip, uid)
        if not result:
            connection_failures += 1
            current_app.logger.debug("DEBUG: Connection failure {}".format(connection_failures))
        else:
            connection_failures = 0
        sleep(60)
      
    # If we've had 3 failures, clean up our session and end it.
    active_still_sessions[uid].file.write('\n]')
    active_still_sessions[uid].cleanup()
    return


# -------- Utility --------
def create_new_session(uid):
    if uid not in active_still_sessions:
        active_still_sessions[uid] = PicoStillSession()
    active_still_sessions[uid].uninit = False
    active_still_sessions[uid].start_time = datetime.now()  # Not now, but X samples * 60*RATE sec ago
    active_still_sessions[uid].filepath = still_active_sessions_path().joinpath('{0}#{1}.json'.format(active_still_sessions[uid].start_time.strftime('%Y%m%d_%H%M%S'), uid))
    active_still_sessions[uid].file = open(active_still_sessions[uid].filepath, 'w')
    active_still_sessions[uid].file.write('[\n')
