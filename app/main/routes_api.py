import json, re, uuid
from datetime import datetime
from pathlib import Path
from time import mktime
from flask import *
from flask_socketio import emit
from webargs import fields
from webargs.flaskparser import use_args, FlaskParser
from . import main
from .routes_frontend import get_recipes
from .routes_frontend import get_graph_data
from .. import *

arg_parser = FlaskParser()

# Register: /API/pico/register?uid={UID}
# Response: '#{0}#\r\n' where {0} : T = Registered, F = Not Registered
register_args = {
    'uid': fields.Str(required=True),       #32 character alpha-numeric serial number
}
@main.route('/API/pico/register')
@use_args(register_args, location='querystring')
def process_register(args):
    return '#T#\r\n'

# Change State: /API/pico/picoChangeState?picoUID={UID}&state={STATE}
#     Response: '\r\n'
change_state_args = {
    'picoUID': fields.Str(required=True),   #32 character alpha-numeric serial number
    'state': fields.Int(required=True),     #2 = Ready, 3 = Brewing, 4 = Sous Vide, 5 = Rack Beer, 6 = Rinse, 7 = Deep Clean, 9 = De-Scale
}
@main.route('/API/pico/picoChangeState')
@use_args(change_state_args, location='querystring')
def process_change_state_request(args):
    if args['state'] in [3, 4, 7]:
        create_new_session()
    return '\r\n'

# Check Firmware: /API/pico/checkFirmware?uid={UID}&version={VERSION}
#       Response: '#{0}#' where {0} : T = Update Available, F = No Updates
check_firmware_args = {
    'uid': fields.Str(required=True),       #32 character alpha-numeric serial number
    'version': fields.Str(required=True),   #Current firmware version - i.e. 0.1.11
}
@main.route('/API/pico/checkFirmware')
@use_args(check_firmware_args, location='querystring')
def process_check_firmware(args):
    return '#F#'

# Get Firmware: /API/pico/getFirmware?uid={UID}
#     Response: RAW Bin File
#get_firmware_args = {
#    'uid': fields.Str(required=True),       #32 character alpha-numeric serial number
#}
#@main.route('/API/pico/getFirmware')
#@use_args(get_firmware_args, location='querystring')
#def process_get_firmware(args):
#    pass

# Actions Needed: /API/pico/getActionsNeeded?uid={UID}
#       Response: '#{0}#' where {0} : Empty = None, 7 = Deep Clean
actions_needed_args = {
    'uid': fields.Str(required=True),       #32 character alpha-numeric serial number
}
@main.route('/API/pico/getActionsNeeded')
@use_args(actions_needed_args, location='querystring')
def process_get_actions_needed(args):
    #TODO : Respond with periodic Deep Clean?
    return '##'

#    Error: /API/pico/error?uid={UID}&rfid={RFID}
# Response: '\r\n'
error_args = {
    'uid': fields.Str(required=True),       #32 character alpha-numeric serial number
    'rfid': fields.Str(required=True),      #14 character alpha-numeric PicoPak RFID (could be blank)
}
@main.route('/API/pico/error')
@use_args(error_args, location='querystring')
def process_error(args):
    #TODO: Error Processing?
    return '\r\n'

# Get Session: /API/pico/getSession?uid={UID}&sesType={SESSION_TYPE}
#    Response: '#{0}#\r\n' where {0} : 20 character alpha-numeric session id
get_session_args = {
    'uid': fields.Str(required=True),       #32 character alpha-numeric serial number
    'sesType': fields.Int(required=True),   #0 = Brewing (never happens since session = 14 alpha-numeric RFID), 1 = Deep Clean, 2 = Sous Vide, 4 = Cold Brew, 5 = Manual Brew
}
@main.route('/API/pico/getSession')
@use_args(get_session_args, location='querystring')
def process_get_session(args):
    current_session.uid = uuid.uuid4().hex[:20]
    if args['sesType'] == 1:
        current_session.name = 'Deep Clean'
    elif args['sesType'] == 2:
        current_session.name = 'Sous Vide'
    elif args['sesType'] == 4:
        current_session.name = 'Cold Brew'
    elif args['sesType'] == 5:
        current_session.name = 'Manual Brew'
        create_new_session()
    else:
        current_session.name = 'Unknown'
    return '#{0}#\r\n'.format(current_session.uid)

# Recipe List: /API/pico/recipelist?uid={UID}
#    Response: '#{0}#\r\n\r\n' where {0} : ??
recipe_list_args = {
    'uid': fields.Str(required=True),       #32 character alpha-numeric serial number
}
@main.route('/API/pico/recipelist')
@use_args(recipe_list_args, location='querystring')
def process_recipe_list(args):
    #TODO: Never Captured with an actual recipe list
    return '##\r\n\r\n'

# Associated Paks: /API/pico/getAssociatedPaks?uid={UID}
#        Response: '\r\n#{0}#\r\n\r\n' where {0} : [14 character alpha-numeric PicoPak Tag,Name|]+
associated_paks_args = {
    'uid': fields.Str(required=True),       #32 character alpha-numeric serial number
}
@main.route('/API/pico/getAssociatedPaks')
@use_args(associated_paks_args, location='querystring')
def process_associated_paks(args):
    return '\r\n#{0}#\r\n\r\n'.format(get_recipe_list())

#   Recipe: /API/pico/getRecipe?uid={UID}&rfid={RFID}&ibu={IBU}&abv={ABV}
# Response: '{0}' where : #NAME/IBU_TWEAK,ABV_TWEAK,ABV,IBU,[TEMPERATURE,STEP_TIME,DRAIN_TIME,LOCATION,STEP_NAME]+,|128x64 2048 byte OLED Image (http://javl.github.io/image2cpp/)|#
get_recipe_args = {
    'uid': fields.Str(required=True),       #32 character alpha-numeric serial number
    'rfid': fields.Str(required=True),      #14 character alpha-numeric PicoPak RFID
    'ibu': fields.Str(required=True),       #Decimal IBU Tweak (i.e. -1, ignore -> not supported)
    'abv': fields.Str(required=True),       #Decimal ABV Tweak (i.e. -1.0, ignore -> not supported)
}
@main.route('/API/pico/getRecipe')
@use_args(get_recipe_args, location='querystring')
def process_get_recipe(args):
    #TODO: figure out what to do with IBU/ABV tweaks
    return '#{0}#'.format(get_recipe_by_id(args['rfid']))

#       Log: /API/pico/log?uid={UID}&sesId={SID}&wort={TEMP}&therm={TEMP}&step={STEP_NAME}&[event={STEP_NAME}&]error={ERROR}&sesType={SESSION_TYPE}&timeLeft={TIME}&shutScale={SS}
#  Response: '\r\n\r\n'
log_args = {
    'uid': fields.Str(required=True),       #32 character alpha-numeric serial number
    'sesId': fields.Str(required=True),     #10/24 character alphanumeric session id (10 = Brew/24 = Deep Clean/Sous Vide)
    'wort': fields.Str(required=True),      #Integer Temperature
    'therm': fields.Str(required=True),     #Integer Temperature
    'step': fields.Str(required=True),      #HTTP formatted step name (Preparing%20to%20Brew)
    'event': fields.Str(required=False),    #HTTP formatted step name (Preparing%20to%20Brew) : only occurs when new steps start
    'error': fields.Str(required=True),     #Integer error number
    'sesType': fields.Str(required=True),   #0 = Brewing, 1 = Deep Clean, 2 = Sous Vide
    'timeLeft': fields.Str(required=True),  #Integer (Seconds Left?)
    'shutScale': fields.Str(required=True), #%0.2f
}
@main.route('/API/pico/log')
@use_args(log_args, location='querystring')
def process_log(args):
    session_data = {'time': ((datetime.utcnow()-datetime(1970,1,1)).total_seconds() * 1000), #(mktime(datetime.utcnow().timetuple()) * 1000),
                    'timeLeft': args['timeLeft'],
                    'step': args['step'],
                    'wort': args['wort'],
                    'therm': args['therm'],
                    }
    event = None
    if 'event' in args:
        event = args['event']
        session_data.update({'event': event})
    json.dump(session_data, current_session.file)
    current_session.step = args['step']
    current_session.data.append(session_data)
    graph_update = json.dumps({'time': session_data['time'], 'wort': int(session_data['wort']), 'therm': int(session_data['therm']), 'session': current_session.name, 'step': current_session.step, 'event': event})
    socketio.emit('session_update', graph_update)

    if re.search('complete', args['step'], re.IGNORECASE):
        current_session.file.write('\n]')
        current_session.file.close()
    else:
        current_session.file.write(',\n\t')
    return '\r\n\r\n'

# -------- Utility --------
def get_recipe_by_id(recipe_id):
    recipe = next((r for r in get_recipes() if r.id == recipe_id), None)
    current_session.uid = recipe.id
    current_session.name = recipe.name
    return recipe.serialize()

def get_recipe_list():
    recipe_list = ''
    for r in get_recipes():
        recipe_list += r.id + ',' + r.name + '|'
    return recipe_list

def create_new_session():
    session_dir = Path(SESSION_PATH)
    session_dir.mkdir(parents=True, exist_ok=True)
    filename = '{0}#{1}#{2}.json'.format(datetime.now().strftime('%Y%m%d_%H%M%S'), current_session.uid, current_session.name.replace(' ', '_'))
    current_session.filename = str(session_dir.joinpath(filename))
    current_session.file = open(current_session.filename, 'w')
    current_session.file.write('[\n\t')
