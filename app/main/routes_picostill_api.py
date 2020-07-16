import json
import uuid
import os
from datetime import datetime
from flask import current_app, request, Response, abort, send_from_directory
from webargs import fields
from webargs.flaskparser import use_args, FlaskParser
from enum import Enum
from random import seed, randint

from .. import socketio
from . import main
from .config import picostill_firmware_path
from .firmware import MachineType, firmware_filename, firmware_upgrade_required, minimum_firmware
from .model import PicoBrewSession
from .routes_frontend import get_zseries_recipes, load_brew_sessions
from .session_parser import active_brew_sessions


arg_parser = FlaskParser()
seed(1)

events = {}


# Get Firmware: /firmware/picostill/<version>
#     Response: RAW Bin File
@main.route('/firmware/picostill/<file>', methods=['GET'])
def process_picostill_firmware(file):
    current_app.logger.debug('DEBUG: PicoStill fetch firmware file={}'.format(file))
    return send_from_directory(picostill_firmware_path(), file)


# Check Firmware: /API/PicoStill/getFirmwareAddress?uid={UID}&version={VERSION}
#       Response: '#{0}#' where {0} : {URL} = Url of firmware, F = No Updates
picostill_check_firmware_args = {
    'uid': fields.Str(required=True),       # 32 character alpha-numeric serial number
    'version': fields.Str(required=True),   # Current firmware version - i.e. 0.0.30
}
@main.route('/API/PicoStill/getFirmwareAddress', methods=['GET'])
@use_args(picostill_check_firmware_args, location='querystring')
def process_picostill_check_firmware(args):
    if firmware_upgrade_required(MachineType.PICOSTILL, args['version']):
        filename = firmware_filename(MachineType.PICOSTILL, minimum_firmware(MachineType.PICOSTILL))
        return '#https://picobrew.com/firmware/picostill/{}#'.format(filename)
    return '#F#'
