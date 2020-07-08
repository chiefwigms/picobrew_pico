import json
import uuid
import os
from datetime import datetime
from webargs import fields
from webargs.flaskparser import use_args, FlaskParser

from .. import socketio
from . import main
from .config import brew_active_sessions_path
from .model import PicoBrewSession
from .routes_frontend import get_zymatic_recipes
from .session_parser import active_brew_sessions


arg_parser = FlaskParser()
events = {}

# usersetup: /API/usersetup?machine={}&admin=0
#             Response: '\r\n#{0}/{1}|#' where {0} : Profile GUID, {1} = User Name
user_setup_args = {
    'machine': fields.Str(required=True),       # 12 character alpha-numeric Product ID
    'admin': fields.Int(required=True),         # Always 0
}
@main.route('/API/usersetup')
@use_args(user_setup_args, location='querystring')
def process_user_setup(args):
    profile_guid = uuid.uuid4().hex[:32]
    user_name = "DefaultUser"  # TODO: Config parameter?
    return '\r\n#{}/{}|#'.format(profile_guid, user_name)


# firstSetup: /API/firstSetup?machine={}|1W_ADDR,1/1W_ADDR,2/1W_ADDR,3/1W_ADDR,4&admin=0
#             Response: '\r\n'
first_setup_args = {
    'machine': fields.Str(required=True),       # 12 character alpha-numeric Product ID (1W_ADDR = 16 character alpha-numeric OneWire Address, i.e. 28b0123456789abc)
    'admin': fields.Int(required=True),         # Always 0
}
@main.route('/API/firstSetup')
@use_args(first_setup_args, location='querystring')
def process_first_setup(args):
    return '\r\n'


# zymaticFirmwareCheck: /API/zymaticFirmwareCheck?machine={}&ver={}&maj={}&min={}
#             Response: '\r\n#{0}#\r\n' where {0} : T/F if newer firmware available
zymatic_firmware_check_args = {
    'machine': fields.Str(required=True),       # 12 character alpha-numeric Product ID
    'ver': fields.Int(required=True),           # Int Version
    'maj': fields.Int(required=True),           # Int Major Version
    'min': fields.Int(required=True),           # Int Minor Version
}
@main.route('/API/zymaticFirmwareCheck')
@use_args(zymatic_firmware_check_args, location='querystring')
def process_zymatic_firmware_check(args):
    return '\r\n#F#\r\n'


# SyncUser: /API/SyncUser?user={}&machine={}
# Response: '\r\n\r\n#{0}#' where {0} : Cleaning/Recipe List
sync_user_args = {
    'user': fields.Str(required=True),          # 32 character alpha-numeric Profile GUID
    'machine': fields.Str(required=True),       # 12 character alpha-numeric Product ID
}
@main.route('/API/SyncUser')
@main.route('/API/SyncUSer')
@use_args(sync_user_args, location='querystring')
def process_sync_user(args):
    if args['user'] == '00000000000000000000000000000000':
        # New Clean V6
        # -Make sure that all 3 mash screens are in place in the step filter. Do not insert the adjunct loaf/hop cages.
        # -Place cleaning tablet in the right area of the adjunct compartment, on top of the smaller screen, at the end of the metal tab. 1/4 cup of powdered dishwasher detergent can also be used.
        # -Add 1.5 gallons of HOT tap water to the keg at completion of cleaning cycle (prompt notes/before final step) -Empty and rinse keg, step filter, screens, and in-line filter.
        # -Fill keg with 4 gallons of hot tap water
        # -Connect black fitting to 'OUT' post on keg
        # -Attach wand to grey fitting and run it into bucket or sink, OR attach grey fitting to 'IN' post on empty keg
        # -Continue, this will rinse your system. There should be no water left in the keg at the end of this step.
        # Share your experience with info@picobrew.com, Subject - New Clean Beta attn: Kevin, attach pictures of debris removed and collected on screens if possible.
        return '\r\n\r\n#Cleaning v1/7f489e3740f848519558c41a036fe2cb/Heat Water,152,0,0,0/Clean Mash,152,15,1,5/Heat to Temp,152,0,0,0/Adjunct,152,3,2,1/Adjunct,152,2,3,1/Adjunct,152,2,4,1/Adjunct,152,2,5,1/Heat to Temp,197,0,0,0/Clean Mash,197,10,1,0/Clean Mash,197,2,1,0/Clean Adjunct,197,2,2,0/Chill,120,10,0,2/|Rinse v3/0160275741134b148eff90acdd5e462f/Rinse,0,2,0,5/|New Clean Beta v6/c66b2c4f4a3f42fb8180c795d0d01813/Fill Mash,0,5,1,0/Balance Temps,0,5,5,0/Heat to 120,120,0,0,0/120,120,20,5,0/Heat to 140,140,0,0,0/140,140,35,5,0/Mash,0,5,1,0/Balance Temps,0,3,0,0/140,140,5,5,0/160,160,5,5,0/175,175,5,5,0/Heat to 200,197,0,0,0/200,197,19,5,0/Mash,0,3,1,0/Balance Temps,0,3,0,0/Cool,120,3,5,0/Mash,0,5,1,8/See RecP Notes,0,0,6,0/Flush System,0,12,5,0/|#'
    else:
        # Brew Recipes
        return '\r\n\r\n#{0}#'.format(get_zymatic_recipe_list())


# checksync: /API/checksync?user={}
#  Response: '\r\n#!#' or '\r\n#+#'
check_sync_args = {
    'user': fields.Str(required=True),          # 32 character alpha-numeric Profile GUID
}
@main.route('/API/checksync')
@use_args(check_sync_args, location='querystring')
def process_check_sync(args):
    # Needs Sync '\r\n#+#'
    #    No Sync '\r\n#!#'
    return '\r\n#!#'


# recoversession: /API/recoversession?session={}&code={}
#       Response: '\r\n#{0}!#' where {0} = Recipe String or '\r\n#{0}#' where {0} = Recovery Step
recover_session_args = {
    'session': fields.Str(required=True),       # 32 character alpha-numeric session
    'code': fields.Int(required=True),          # 0 = Step 1, 1 = Step 2
}
@main.route('/API/recoversession')
@use_args(recover_session_args, location='querystring')
def process_recover_session(args):
    session = args['session']
    uid = get_machine_by_session(session)
    if args['code'] == 0:
        return '\r\n#{0}!#'.format(get_recipe_by_name(active_brew_sessions[uid].name))
    else:
        return '\r\n#{0}#'.format(active_brew_sessions[uid].recovery)


# sessionerror: /API/sessionerror?machine={}&session={}&errorcode={}
#     Response: '\r\n'
session_error_args = {
    'machine': fields.Str(required=True),       # 12 character alpha-numeric Product ID
    'session': fields.Str(required=True),       # 32 character alpha-numeric session
    'code': fields.Int(required=True),          # Int Error Code
}
@main.route('/API/sessionerror')
@use_args(session_error_args, location='querystring')
def process_session_error(args):
    # TODO: What to do?
    return '\r\n'


#  logsession: /API/logSession?user={}&recipe={}&code={}&machine={}&firm={}
#              /API/logsession?session={}&code=1&data={}&state={}
#              /API/LogSession?session={}&data={}&code=2&step={}&state={}
#              /API/logsession?session={}&code=3
#    Response: '\r\n#{0}#' where {0} = Session or '\r\n'
log_session_args = {
    'user': fields.Str(required=False),          # 32 character alpha-numeric Profile GUID
    'recipe': fields.Str(required=False),        # 32 character alpha-numeric recipe
    'code': fields.Int(required=True),           # 0 = New Session, 1 = Event, 2 = Temperature Data, 3 = End Session
    'machine': fields.Str(required=False),       # 12 character alpha-numeric Product ID
    'firm': fields.Str(required=False),          # Current firmware version - i.e. 0.1.14
    'session': fields.Str(required=False),       # 32 character alpha-numeric session
    'data': fields.Str(required=False),          # Event Name / Temperature Data, HTTP Formatted (i.e. %20 ( ) or %2F = (/))
    'state': fields.Int(required=False),         # ?
    'step': fields.Str(required=False),          # 8 Integers separated by / for recovery
}
@main.route('/API/logsession')
@main.route('/API/logSession')
@main.route('/API/LogSession')
@use_args(log_session_args, location='querystring')
def process_log_session(args):
    ret = '\r\n'
    global events
    if args['code'] == 0:
        uid = args['machine']
        if uid not in active_brew_sessions:
            active_brew_sessions[uid] = PicoBrewSession()
        active_brew_sessions[uid].session = uuid.uuid4().hex[:32]
        active_brew_sessions[uid].name = get_recipe_name_by_id(args['recipe'])
        active_brew_sessions[uid].filepath = brew_active_sessions_path().joinpath('{0}#{1}#{2}#{3}.json'.format(datetime.now().strftime('%Y%m%d_%H%M%S'), uid, active_brew_sessions[uid].session, active_brew_sessions[uid].name.replace(' ', '_')))
        active_brew_sessions[uid].file = open(active_brew_sessions[uid].filepath, 'w')
        active_brew_sessions[uid].file.write('[')
        active_brew_sessions[uid].file.flush()
        ret = '\r\n#{0}#'.format(active_brew_sessions[uid].session)
    elif args['code'] == 1:
        session = args['session']
        if session not in events:
            events[session] = []
        events[session].append(args['data'])
        uid = get_machine_by_session(session)
        active_brew_sessions[uid].step = args['data']
    elif args['code'] == 2:
        session = args['session']
        uid = get_machine_by_session(session)
        temps = [int(temp[2:]) for temp in args['data'].split('|')]
        session_data = {'time': ((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000),
                        'heat1': temps[0],
                        'wort': temps[1],
                        'board': temps[2],
                        'heat2': temps[3],
                        'step': active_brew_sessions[uid].step,
                        'recovery': args['step'],
                        'state': args['state'],
                        }
        event = None
        if session in events and len(events[session]) > 0:
            if len(events[session]) > 1:
                print('DEBUG: Zymatic events > 1 - size = {}'.format(len(events[session])))
            event = events[session].pop(0)
            session_data.update({'event': event})
        active_brew_sessions[uid].data.append(session_data)
        active_brew_sessions[uid].recovery = args['step']
        graph_update = json.dumps({'time': session_data['time'],
                                   'data': temps,
                                   'session': active_brew_sessions[uid].name,
                                   'step': active_brew_sessions[uid].step,
                                   'event': event,
                                   })
        socketio.emit('brew_session_update|{}'.format(uid), graph_update)
        active_brew_sessions[uid].file.write('\n\t{},'.format(json.dumps(session_data)))
        active_brew_sessions[uid].file.flush()
    else:
        session = args['session']
        uid = get_machine_by_session(session)
        active_brew_sessions[uid].file.seek(0, os.SEEK_END)
        active_brew_sessions[uid].file.seek(active_brew_sessions[uid].file.tell() - 1, os.SEEK_SET)  # Remove trailing , from last data set
        active_brew_sessions[uid].file.write('\n]')
        active_brew_sessions[uid].cleanup()
    return ret


# -------- Utility --------
def get_zymatic_recipe_list():
    recipe_list = ''
    for r in get_zymatic_recipes():
        recipe_list += r.serialize()
    return recipe_list


def get_recipe_name_by_id(recipe_id):
    recipe = next((r for r in get_zymatic_recipes() if r.id == recipe_id), None)
    return 'Invalid Recipe' if not recipe else recipe.name


def get_recipe_by_name(recipe_name):
    recipe = next((r for r in get_zymatic_recipes() if r.name == recipe_name), None)
    return '' if not recipe else recipe.serialize()


def get_machine_by_session(session):
    return next((uid for uid in active_brew_sessions if active_brew_sessions[uid].session == session), None)
