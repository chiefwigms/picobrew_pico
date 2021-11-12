import json
from datetime import datetime
from webargs import fields
from webargs.flaskparser import use_args, FlaskParser
from flask import request
from marshmallow import INCLUDE

from . import main
from .. import socketio
from .config import iSpindel_active_sessions_path
from .model import iSpindelSession
from .session_parser import active_iSpindel_sessions
from .units import convert_temp, epoch_time, excel_date
from .webhook import send_webhook


arg_parser = FlaskParser()

iSpindel_dataset_args = {
    'name': fields.Str(required=False),  # device name
    'ID': fields.Int(required=True),  # random device ID
    'angle': fields.Float(required=False),  # device floatation angle
    'temperature': fields.Float(required=True),  # device temperature
    'temp_units': fields.Str(required=True),  # temperature units in C or F
    'battery': fields.Float(required=True),  # device battery voltage
    'gravity': fields.Float(required=True),  # calculated specific gravity
    'interval': fields.Int(required=False),  # sampling interval in seconds
    'RSSI': fields.Int(required=False)  # RSSI of WiFi signal
}

# Process iSpindel Data: /API/iSpindel or /API/iSpindle


@main.route('/API/iSpindle', methods=['POST'])
@main.route('/API/iSpindel', methods=['POST'])
@use_args(iSpindel_dataset_args, unknown=INCLUDE)
def process_iSpindel_data(data):
    uid = str(data['ID'])

    if uid not in active_iSpindel_sessions:
        active_iSpindel_sessions[uid] = iSpindelSession()

    if active_iSpindel_sessions[uid].active:
        # initialize session and session files
        if active_iSpindel_sessions[uid].uninit:
            create_new_session(uid)

        time = datetime.utcnow()
        session_data = []
        log_data = ''
        point = {
            'time': epoch_time(time),
            'temp': data['temperature'] if data['temp_units'] == 'F' else convert_temp(data['temperature'], 'F'),
            'gravity': data['gravity'],
        }

        session_data.append(point)
        log_data += '\n\t{},'.format(json.dumps(point))

        # send data to configured webhooks (logging error and tracking individual status)
        for webhook in active_iSpindel_sessions[uid].webhooks:
            # translate point into Tilt-like webhook data payload
            webhook_data = {
                'Timepoint': excel_date(time),
                'Temp': point['temp'],
                'SG': point['gravity'],
                'color': data['name']
            }
            # send and update status of webhook
            send_webhook(webhook, webhook_data)

        active_iSpindel_sessions[uid].data.extend(session_data)
        active_iSpindel_sessions[uid].voltage = str(data['battery']) + 'V'

        graph_update = json.dumps({'voltage': data['battery'], 'data': session_data})
        socketio.emit('iSpindel_session_update|{}'.format(data['ID']), graph_update)

        # end fermentation only when user specifies fermentation is complete
        if (active_iSpindel_sessions[uid].uninit == False and active_iSpindel_sessions[uid].active == False):
            active_iSpindel_sessions[uid].file.write('{}\n\n]'.format(log_data[:-2]))
            active_iSpindel_sessions[uid].cleanup()
            return('', 200)
        else:
            active_iSpindel_sessions[uid].active = True
            active_iSpindel_sessions[uid].file.write(log_data)
            active_iSpindel_sessions[uid].file.flush()
            return('', 200)
    else:
        return('', 200)

# -------- Utility --------


def create_new_session(uid):
    if uid not in active_iSpindel_sessions:
        active_iSpindel_sessions[uid] = iSpindelSession()
    active_iSpindel_sessions[uid].uninit = False
    active_iSpindel_sessions[uid].start_time = datetime.now()  # Not now, but X samples * 60*RATE sec ago
    active_iSpindel_sessions[uid].filepath = iSpindel_active_sessions_path().joinpath('{0}#{1}.json'.format(active_iSpindel_sessions[uid].start_time.strftime('%Y%m%d_%H%M%S'), uid))
    active_iSpindel_sessions[uid].file = open(active_iSpindel_sessions[uid].filepath, 'w')
    active_iSpindel_sessions[uid].file.write('[')
