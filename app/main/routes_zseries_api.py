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
from .config import brew_active_sessions_path, zseries_firmware_path
from .model import PicoBrewSession
from .routes_frontend import get_zseries_recipes, load_brew_sessions
from .session_parser import active_brew_sessions


arg_parser = FlaskParser()
seed(1)

events = {}

latest_firmware = {
    "version": "0.0.116",
    "source": "https://picobrew.com/firmware/zseries/zseries_0_0_116.bin"
}


class SessionType(int, Enum):
    RINSE = 0
    CLEAN = 1
    DRAIN = 2
    RACK_BEER = 3
    CIRCULATE = 4
    SOUS_VIDE = 5
    BEER = 6
    COFFEE = 12
    CHILL = 13


class ZProgramId(int, Enum):
    RINSE = 1
    DRAIN = 2
    RACK_BEER = 3
    CIRRCULATE = 4
    SOUS_VIDE = 6
    CLEAN = 12
    BEER_OR_COFFEE = 24
    CHILL = 27


def convertTemp(temp: float, units: str):
    if units.upper() == 'F':
        return (temp * 9/5) + 32  # convert celcius to fahrenheit
    return (temp - 32) * 5/9  # convert fahrenheit to celcius


# Get Firmware: /firmware/zseries/<version>
#     Response: RAW Bin File
@main.route('/firmware/zseries/<file>', methods=['GET'])
def process_zseries_firmware(file):
    current_app.logger.debug('DEBUG: ZSeries fetch firmware file={}'.format(file))
    return send_from_directory(zseries_firmware_path(), file)


# ZState: PUT /Vendors/input.cshtml?type=ZState&token={}
#             Response: '\r\n\r\n#{0}#' where {0} : Machine State Response (firmware, boilertype, session stats, reg token)
zseries_query_args = {
    'type': fields.Str(required=False),          # API request type identifier
    'token': fields.Str(required=True),         # alpha-numeric unique identifier for Z
    'id': fields.Str(required=False),           # alpha-numeric unique identifier for Z session/recipe
    'ctl': fields.Str(required=False)           # recipe list request doesn't use `type` param
}


# ZFetchRecipeSummary: POST /Vendors/input.cshtml?ctl=RecipeRefListController&token={}
#                           Response: '\r\n\r\n#{0}#' where {0} : Recipes Response
# ZSessionUpdate:      POST /Vendors/input.cshtml?type=ZSessionLog&token={}
#                      Response: '\r\n\r\n#{0}#' where {0} : Echo Session Log Request with ID and Date
# ZSession: POST /Vendors/input.cshtml?type=ZSession&token={}&id={}  // id == session_id is only present on "complete session" request
#               Response: '\r\n\r\n#{0}#' where {0} : Machine State Response (firmware, boilertype, session stats, reg token)
@main.route('/Vendors/input.cshtml', methods=['POST'])
@use_args(zseries_query_args, location='querystring')
def process_zseries_post_request(args):
    type = request.args.get('type')
    controller = request.args.get('ctl')

    # current_app.logger.debug('DEBUG: ZSeries POST request args = {}; request = {}'.format(args, request.json))

    if controller == 'RecipeRefListController':
        body = request.json
        ret = {
            "Kind": body['Kind'],
            "MaxCount": body['MaxCount'],
            "Offset": body['Offset'],
            "Recipes": get_zseries_recipe_metadata_list()
        }
        return Response(json.dumps(ret), mimetype='application/json')
    elif type == 'ZSessionLog':
        return update_session_log(request.args.get('token'), request.json)
    elif type == 'ZSession':
        return create_or_close_session(request)
    else:
        abort(404)


# ZState:   PUT /Vendors/input.cshtml?type=ZState&token={}
#               Response: '\r\n\r\n#{0}#' where {0} : Machine State Response (firmware, boilertype, session stats, reg token)
# ZSession: PUT /Vendors/input.cshtml?type=ZSession&token={}&id={}  // id == session_id is only present on "complete session" request
#               Response: '\r\n\r\n#{0}#' where {0} : Machine State Response (firmware, boilertype, session stats, reg token)
@main.route('/Vendors/input.cshtml', methods=['PUT'])
@use_args(zseries_query_args, location='querystring')
def process_zseries_put_request(args):
    type = request.args.get('type')
    if type == 'ZState' and request.json['CurrentFirmware']:
        return process_zstate(request)
    elif type == 'ZSession':
        return create_or_close_session(request)
    else:
        abort(404)


# ZRecipeDetails:   GET /Vendors/input.cshtml?type=Recipe&token={}&id={} // id == recipe_id
#                       Response: '\r\n\r\n#{0}#' where {0} : Remaining Recipe Steps (based on last session update from machine)
# ZResumeSession:   GET /Vendors/input.cshtml?type=ResumableSession&token={}&id={} // id == session_id
#                       Response: '\r\n\r\n#{0}#' where {0} : Remaining Recipe Steps (based on last session update from machine)
@main.route('/Vendors/input.cshtml', methods=['GET'])
@use_args(zseries_query_args, location='querystring')
def process_zseries_get_request(args):
    type = request.args.get('type')
    identifier = request.args.get('id')

    # current_app.logger.debug('DEBUG: ZSeries GET request args = {};'.format(args))

    if type == 'Recipe' and identifier is not None:
        return process_recipe_request(identifier)
    elif type == 'ResumableSession' and identifier is not None:
        return process_recover_session(request.args.get('token'), identifier)
    else:
        abort(404)


# GET /Vendors/input.cshtml?type=Recipe&token={}&id={} // id == recipe_id
def process_recipe_request(recipe_id):
    recipe = get_recipe_by_id(recipe_id)
    return recipe.serialize()


# checksync: /Vendors/input.cshtml?type=ZState&token=<token>
#  Request:    { "BoilerType": 1|2, "CurrentFirmware": "1.2.3" }
#  Response (example):
#              {
#                   "Alias": "ZSeries",
#                   "BoilerType": 1,
#                   "CurrentFirmware": "0.0.116",
#                   "IsRegistered": true,
#                   "IsUpdated": true,
#                   "ProgramUri": null,
#                   "RegistrationToken": "-1",
#                   "SessionStats": {
#                       "DirtySessionsSinceClean": 1,
#                       "LastSessionType": 5,
#                       "ResumableSessionID": -1
#                   },
#                   "TokenExpired": false,
#                   "UpdateAddress": "-1",
#                   "UpdateToFirmware": null,
#                   "ZBackendError": 0
#               }
def process_zstate(args):
    json = request.json
    update_required = json['CurrentFirmware'] != latest_firmware['version']
    uid = request.args['token']

    returnVal = {
        "Alias": "ZSeries",
        "BoilerType": json['BoilerType'],       # TODO sometimes machine loses boilertype, need to resync with known state
        "IsRegistered": True,                   # likely we don't care about registration with BYOS
        "IsUpdated": False if update_required else True,
        "ProgramUri": None,                     # what is this?
        "RegistrationToken": -1,
        "SessionStats": {
            "DirtySessionsSinceClean": dirty_sessions_since_clean(uid),
            "LastSessionType": last_session_type(uid),
            "ResumableSessionID": resumable_session_id(uid)
        },
        "UpdateAddress": latest_firmware['source'] if update_required else "-1",
        "UpdateToFirmware": None,
        "ZBackendError": 0
    }
    return returnVal


def dirty_sessions_since_clean(uid):
    brew_sessions = get_archived_sessions_by_machine(uid)
    post_clean_sessions = []
    clean_found = False
    for s in brew_sessions:
        session_type = SessionType(s['type'])
        if (session_type == SessionType.CLEAN):
            clean_found = True

        if (not clean_found and session_type in [SessionType.BEER.value, SessionType.COFFEE.value, SessionType.SOUS_VIDE.value]):
            post_clean_sessions.append(s)

    return len(post_clean_sessions)


def last_session_type(uid):
    brew_sessions = get_archived_sessions_by_machine(uid)

    if len(brew_sessions) == 0:
        return SessionType.CLEAN
    else:
        last_session = brew_sessions[0]
        # just assume last session was a rinse session (session after a brew)
        session_type = SessionType(last_session['type']) if last_session['type'] is not None else SessionType.RINSE
        return session_type


def resumable_session_id(uid):
    if uid not in active_brew_sessions:
        return -1
    return active_brew_sessions[uid].id


def create_or_close_session(args):
    session_id = request.args.get('id')

    if session_id:
        return close_session(request.args.get('token'), session_id, request.json)
    else:
        return create_session(request.args.get('token'), request.json)


# checksync: /Vendors/input.cshtml?type=ZSession&token=<token>&id=<session_id>
#  Request (example - beer session):
#              {
#                   "DurationSec": 11251,
#                   "FirmwareVersion": "0.0.119",
#                   "GroupSession": true,
#                   "MaxTemp": 98.22592515,
#                   "MaxTempAddedSec": 0,
#                   "Name": "All Good Things",
#                   "PressurePa": 101975.6172,
#                   "ProgramParams": {
#                       "Abv": -1,              # not a customization feature on the Z
#                       "Duration": 0,
#                       "Ibu": -1,
#                       "Intensity": 0,
#                       "Temperature": 0,
#                       "Water": 13.1
#                   },
#                   "RecipeID": "150xxx",
#                   "SessionType": 6,           # see options in SessionType
#                   "ZProgramId": 24            # see options in ZProgram
#               }
# #  Response (example - begin session):
#              {
#                   "Active": false,
#                   "CityLat": xx.xxxxxx,
#                   "CityLng": -yyy.yyyyyy,
#                   "ClosingDate": "2020-05-04T19:54:58.74",
#                   "CreationDate": "2020-05-04T19:46:04.153",
#                   "Deleted": false,
#                   "DurationSec": 578,
#                   "FirmwareVersion": "0.0.119",
#                   "GUID": "<all upper case machine guid>",
#                   "GroupSession": false,
#                   "ID": <session-id>,
#                   "LastLogID": 11407561,
#                   "Lat": xx.xxxxxx,
#                   "Lng": -yyy.yyyyyy,
#                   "MaxTemp": 98.24455443,
#                   "MaxTempAddedSec": 0,
#                   "Name": "RINSE",
#                   "Notes": null,
#                   "Pressure": 0,
#                   "ProfileID": zzzz,
#                   "ProgramParams": {
#                       "Abv": null,              # not a customization feature on the Z
#                       "Duration": 0.0,
#                       "Ibu": null,
#                       "Intensity": 0.0,
#                       "Temperature": 0.0,
#                       "Water": 0.0
#                   },
#                   "RecipeGuid": null,
#                   "RecipeID": null,
#                   "SecondsRemaining": 0,
#                   "SessionLogs": [],
#                   "SessionType": 0,
#                   "StillUID": null,
#                   "StillVer": null,
#                   "ZProgramId": 1,
#                   "ZSeriesID": www
#               }
def create_session(token, body):
    uid = token                # token uniquely identifies the machine
    recipe = get_recipe_by_name(body['Name'])

    # error out if recipe isn't known where session is beer type (ie 6)
    # due to rinse, rack beer, clean, coffee, sous vide, etc not having server known "recipes"
    if recipe is None and body['SessionType'] == SessionType.BEER:
        error = {
            'error': 'recipe \'{}\' not found - unable to start session'.format(body['Name'])
        }
        return Response(json.dumps(error), status=404, mimetype='application/json')
    elif recipe:
        current_app.logger.debug('recipe for session: {}'.format(recipe.serialize()))

    if uid not in active_brew_sessions:
        active_brew_sessions[uid] = PicoBrewSession()

    session_guid = uuid.uuid4().hex[:32]
    session_id = increment_session_id(uid)

    active_brew_sessions[uid].session = session_guid
    active_brew_sessions[uid].id = session_id
    active_brew_sessions[uid].created_at = datetime.utcnow().isoformat()
    active_brew_sessions[uid].name = recipe.name if recipe else body['Name']
    active_brew_sessions[uid].type = body['SessionType']
    active_brew_sessions[uid].filepath = brew_active_sessions_path().joinpath('{0}#{1}#{2}#{3}#{4}.json'.format(datetime.now().strftime('%Y%m%d_%H%M%S'), uid, active_brew_sessions[uid].session, active_brew_sessions[uid].name.replace(' ', '_'), active_brew_sessions[uid].type))

    current_app.logger.debug('ZSeries - session file created {}'.format(active_brew_sessions[uid].filepath))

    if session_id not in events:
        events[session_id] = []

    active_brew_sessions[uid].file = open(active_brew_sessions[uid].filepath, 'w')
    active_brew_sessions[uid].file.write('[')
    active_brew_sessions[uid].file.flush()

    ret = {
        "Active": False,
        "ClosingDate": None,
        "CreationDate": active_brew_sessions[uid].created_at,
        "Deleted": False,
        "DurationSec": body['DurationSec'],
        "FirmwareVersion": body['FirmwareVersion'],
        "GroupSession": False,      # need to capture traffic from a Z2+ setup for group brewing
        "GUID": active_brew_sessions[uid].session,
        "ID": active_brew_sessions[uid].id,
        "LastLogID": active_brew_sessions[uid].id,
        "MaxTemp": body['MaxTemp'],
        "MaxTempAddedSec": body['MaxTempAddedSec'],
        "Name": active_brew_sessions[uid].name,
        "Notes": None,
        "Pressure": 0,              # is this related to an attached picostill?
        "ProfileID": 28341,         # how to get the userId
        "SecondsRemaining": 0,
        "SessionLogs": [],
        "SessionType": active_brew_sessions[uid].type,
        "StillUID": None,
        "StillVer": None,
        "ZProgramId": body['ZProgramId'],
        "ZSeriesID": uid
    }
    if 'ProgramParams' in body:
        ret.update({
            "ProgramParams": body['ProgramParams']
        })
    if 'RecipeID' in body:
        ret.update({
            "RecipeGuid": None,
            "RecipeID": body['RecipeID']
        })
    return ret


def update_session_log(token, body):
    session_id = body['ZSessionID']
    uid = get_machine_by_session(session_id)

    if uid is None:
        error = {
            'error': 'machine_id {} session {} does not have a matching active session log'.format(token, session_id)
        }
        return Response(json.dumps(error), status=400, mimetype='application/json')

    active_session = active_brew_sessions[uid]

    if active_session.id == -1:
        # update reference to corrupted active_session
        # upon file load with -1 (assume this is the right session to log with)
        active_session.id = session_id
    elif active_session.id != session_id:   # session_id is hex string; session.id is number
        current_app.logger.warn('WARN: ZSeries reported session_id not active session')

        error = {
            'error': 'matching server log identifier {} does not match requested session_id {}'.format(active_session.id, session_id)
        }
        return Response(json.dumps(error), status=400, mimetype='application/json')

    if active_session not in events:
        events[active_session] = []

    if active_brew_sessions[uid].recovery != body['StepName']:
        events[active_session].append(body['StepName'])

    active_session.step = body['StepName']
    log_time = datetime.utcnow()
    session_data = {
        'time': ((log_time - datetime(1970, 1, 1)).total_seconds() * 1000),
        'timeStr': log_time.isoformat(),
        'timeLeft': body['SecondsRemaining'],
        'step': body['StepName'],
        # temperatures from Z are in celsius vs prior device series
        'target': convertTemp(body['TargetTemp'], 'F'),
        'ambient': convertTemp(body['AmbientTemp'], 'F'),
        'drain': convertTemp(body['DrainTemp'], 'F'),
        'wort': convertTemp(body['WortTemp'], 'F'),
        'therm': convertTemp(body['ThermoBlockTemp'], 'F'),
        'recovery': body['StepName'],
        'position': body['ValvePosition']
    }

    event = None
    if active_session in events and len(events[active_session]) > 0:
        if len(events[active_session]) > 1:
            current_app.logger.debug('DEBUG: ZSeries events > 1 - size = {}'.format(len(events[active_session])))
        event = events[active_session].pop(0)
        session_data.update({'event': event})

    active_brew_sessions[uid].data.append(session_data)
    active_brew_sessions[uid].recovery = body['StepName']
    active_brew_sessions[uid].remaining_time = body['SecondsRemaining']
    # for Z graphs we have more data available: wort, hex/therm, target, drain, ambient
    graph_update = json.dumps({'time': session_data['time'],
                               'data': [session_data['target'], session_data['wort'], session_data['therm'], session_data['drain'], session_data['ambient']],
                               'session': active_brew_sessions[uid].name,
                               'step': active_brew_sessions[uid].step,
                               'event': event,
                               })
    socketio.emit('brew_session_update|{}'.format(uid), graph_update)
    active_brew_sessions[uid].file.write('\n\t{},'.format(json.dumps(session_data)))
    active_brew_sessions[uid].file.flush()

    ret = {
        "ID": randint(0, 10000),
        "LogDate": session_data['timeStr'],
    }
    ret.update(body)
    return ret


def close_session(uid, session_id, body):
    ret = {
        "Active": False,
        "ClosingDate": datetime.utcnow().isoformat(),
        "CreationDate": active_brew_sessions[uid].created_at,
        "Deleted": False,
        "DurationSec": body['DurationSec'],
        "FirmwareVersion": body['FirmwareVersion'],
        "GUID": active_brew_sessions[uid].session,
        "ID": active_brew_sessions[uid].id,
        "LastLogID": active_brew_sessions[uid].id,
        "MaxTemp": body['MaxTemp'],
        "MaxTempAddedSec": body['MaxTempAddedSec'],
        "Name": active_brew_sessions[uid].name,
        "Notes": None,
        "Pressure": 0,              # is this related to an attached picostill?
        "ProfileID": 28341,         # how to get the userId
        "SecondsRemaining": 0,
        "SessionLogs": [],
        "SessionType": body['SessionType'],
        "StillUID": None,
        "StillVer": None,
        "ZProgramId": body['ZProgramId'],
        "ZSeriesID": uid
    }

    if 'ProgramParams' in body:
        ret.update({
            "ProgramParams": body['ProgramParams']
        })
    if 'RecipeID' in body:
        ret.update({
            "RecipeGuid": None,
            "RecipeID": body['RecipeID']
        })

    active_brew_sessions[uid].file.seek(0, os.SEEK_END)
    active_brew_sessions[uid].file.seek(active_brew_sessions[uid].file.tell() - 1, os.SEEK_SET)  # Remove trailing , from last data set
    active_brew_sessions[uid].file.write('\n]')
    active_brew_sessions[uid].cleanup()

    return ret


# GET /Vendors/input.cshtml?type=ResumableSession&token=<token>&id=<session_id> HTTP/1.1
def process_recover_session(token, session_id):
    # TODO can one recover a RINSE / CLEAN or otherwise non-BEER or COFFEE session?
    uid = get_machine_by_session(session_id)

    if uid is None:
        error = {
            'error': 'session_id {} not found to be active - unable to resume session'.format(session_id)
        }
        return Response(json.dumps(error), status=400, mimetype='application/json')

    active_session = active_brew_sessions[uid]

    if active_session.id == session_id:   # session_id is hex string; session.id is number
        recipe = get_recipe_by_name(active_session.name)
        current_step = active_session.recovery
        remaining_time = active_session.remaining_time

        steps = []
        step_found = False
        for s in recipe.steps:
            if (s.name == current_step):
                step_found = True

            if (step_found):
                steps.append(s)

        if (not step_found or len(steps) == 0):
            current_app.logger.warn("most recently logged step not found in linked recipe steps")
            error = {
                'error': 'active brew session\'s most recently logged step not found in linked recipe'
            }
            return Response(json.dumps(error), status=400, mimetype='application/json')

        if (len(steps) >= 1):
            current_app.logger.debug("ZSeries step_count={}, active_step={}, time_remaining={}".format(len(steps), current_step, remaining_time))

            # modify runtime of the first step (most recently active)
            steps[0].step_time = remaining_time
            recipe.steps = steps

        ret = {
            "Recipe": json.loads(recipe.serialize()),
            "SessionID": active_session.id,
            "SessionType": active_session.type,
            "ZPicoRecipe": None                         # does this identity the Z pak recipe?
        }
        return ret
    else:
        error = {
            'error': 'matching server log identifier {} does not match requested session_id {}'.format(active_session.id, session_id)
        }
        return Response(json.dumps(error), status=400, mimetype='application/json')


# -------- Utility --------
def get_zseries_recipe_list():
    recipe_list = []
    for r in get_zseries_recipes():
        recipe_list.append(r)
    return recipe_list


def get_zseries_recipe_metadata_list():
    recipe_metadata = []
    for r in get_zseries_recipes():
        meta = {
            "ID": r.id,
            "Name": r.name,
            "Kind": r.kind_code,
            "Uri": None,
            "Abv": -1,
            "Ibu": -1
        }
        recipe_metadata.append(meta)
    return recipe_metadata


def get_recipe_by_id(recipe_id):
    recipe = next((r for r in get_zseries_recipes() if r.id == int(recipe_id)), None)
    return recipe


def get_recipe_by_name(recipe_name):
    recipe = next((r for r in get_zseries_recipes() if r.name == recipe_name), None)
    return recipe


def increment_session_id(uid):
    return len(get_archived_sessions_by_machine(uid)) + (1 if active_brew_sessions[uid].session != '' else 1)


def get_machine_by_session(session_id):
    return next((uid for uid in active_brew_sessions if active_brew_sessions[uid].session == session_id or active_brew_sessions[uid].id == int(session_id) or active_brew_sessions[uid].id == -1), None)


def get_archived_sessions_by_machine(uid):
    brew_sessions = load_brew_sessions(uid=uid)
    return brew_sessions
