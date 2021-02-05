import json
import os
import re
import requests
import socket
import uuid
from ruamel.yaml import YAML
from flask import current_app, make_response, request, send_file, escape
from pathlib import Path
from os import path
from werkzeug.utils import secure_filename


from . import main
from .config import MachineType, base_path, server_config
from .frontend_common import render_template_with_defaults
from .model import PicoBrewSession, PicoFermSession, PicoStillSession, iSpindelSession
from .recipe_import import import_recipes
from .recipe_parser import PicoBrewRecipe, PicoBrewRecipeImport, ZymaticRecipe, ZymaticRecipeImport, ZSeriesRecipe
from .session_parser import load_iSpindel_session, get_iSpindel_graph_data, load_ferm_session, get_ferm_graph_data, get_brew_graph_data, load_brew_session, active_brew_sessions, active_ferm_sessions, active_iSpindel_sessions, active_still_sessions
from .config import base_path, zymatic_recipe_path, zseries_recipe_path, pico_recipe_path, ferm_archive_sessions_path, brew_archive_sessions_path, iSpindel_archive_sessions_path, MachineType


file_glob_pattern = "[!._]*.json"
yaml = YAML()


# -------- Routes --------
@main.route('/')
def index():
    return render_template_with_defaults('index.html', brew_sessions=load_active_brew_sessions(),
                           ferm_sessions=load_active_ferm_sessions(),
                           iSpindel_sessions=load_active_iSpindel_sessions())



@main.route('/brew_history')
def brew_history():
    return render_template_with_defaults('brew_history.html', sessions=load_brew_sessions(), invalid=get_invalid_sessions('brew'))


@main.route('/ferm_history')
def ferm_history():
    return render_template_with_defaults('ferm_history.html', sessions=load_ferm_sessions(), invalid=get_invalid_sessions('ferm'))


@main.route('/iSpindel_history')
def iSpindel_history():
    return render_template_with_defaults('iSpindel_history.html', sessions=load_iSpindel_sessions(), invalid=get_invalid_sessions('iSpindel'))


@main.route('/zymatic_recipes')
def _zymatic_recipes():
    global zymatic_recipes, invalid_recipes
    zymatic_recipes = load_zymatic_recipes()
    recipes_dict = [json.loads(json.dumps(recipe, default=lambda r: r.__dict__)) for recipe in zymatic_recipes]
    return render_template_with_defaults('zymatic_recipes.html', recipes=recipes_dict, invalid=invalid_recipes.get(MachineType.ZYMATIC, set()))


@main.route('/new_zymatic_recipe', methods=['GET', 'POST'])
def new_zymatic_recipe():
    if request.method == 'POST':
        recipe = request.get_json()
        recipe['id'] = uuid.uuid4().hex[:32]
        filename = zymatic_recipe_path().joinpath('{}.json'.format(recipe['name'].replace(' ', '_')))
        if not filename.exists():
            with open(filename, "w") as file:
                json.dump(recipe, file, indent=4, sort_keys=True)
            return '', 204
        else:
            return 'Recipe Exists!', 418
    else:
        return render_template_with_defaults('new_zymatic_recipe.html')


@main.route('/import_zymatic_recipe', methods=['GET', 'POST'])
def import_zymatic_recipe():
    if request.method == 'POST':
        data = request.get_json()
        guid = data['guid'] # user accountId
        uid = data['uid'] # machine productId
        try:
            # import for picobrew and picobrew_c are the same
            import_recipes(uid, guid, None, MachineType.ZYMATIC)
            return '', 204
        except Exception as e:
            current_app.logger.error(f'import of recipes failed: {e}')
            return getattr(e, 'message', e.args[0]), 400
    else:
        machine_ids = [uid for uid in active_brew_sessions if active_brew_sessions[uid].machine_type == MachineType.ZYMATIC]
        return render_template_with_defaults('import_brewhouse_recipe.html', user_required=True, machine_ids=machine_ids)


@main.route('/update_zymatic_recipe', methods=['POST'])
def update_zymatic_recipe():
    update_recipe = request.get_json()
    files = list(zymatic_recipe_path().glob(file_glob_pattern))
    for filename in files:
        recipe = load_zymatic_recipe(filename)
        if recipe.id == update_recipe['id']:
            recipe.update_recipe(filename, update_recipe)
    return '', 204


@main.route('/delete_zymatic_recipe', methods=['GET', 'POST'])
def delete_zymatic_recipe():
    recipe_id = request.get_json()
    files = list(zymatic_recipe_path().glob(file_glob_pattern))
    for filename in files:
        recipe = load_zymatic_recipe(filename)
        if recipe.id == recipe_id:
            os.remove(filename)
            return '', 204
    return 'Delete Recipe: Failed to find recipe id \"' + recipe_id + '\"', 418


def load_zymatic_recipes():
    files = list(zymatic_recipe_path().glob(file_glob_pattern))
    recipes = [load_zymatic_recipe(file) for file in files]
    return list(sorted(filter(lambda x: x.name != None, recipes), key=lambda x: x.name))


def load_zymatic_recipe(file):
    recipe = ZymaticRecipe()
    parse_recipe(MachineType.ZYMATIC, recipe, file)

    recipe.name_escaped = escape(recipe.name).replace(" ", "_")
    return recipe


def get_zymatic_recipes():
    global zymatic_recipes
    return zymatic_recipes


@main.route('/zseries_recipes')
def _zseries_recipes():
    global zseries_recipes, invalid_recipes
    zseries_recipes = load_zseries_recipes()
    recipes_dict = [json.loads(json.dumps(recipe, default=lambda r: r.__dict__)) for recipe in zseries_recipes]
    return render_template_with_defaults('zseries_recipes.html', recipes=recipes_dict, invalid=invalid_recipes.get(MachineType.ZSERIES, set()))


@main.route('/new_zseries_recipe')
def new_zseries_recipe():
    return render_template_with_defaults('new_zseries_recipe.html')


@main.route('/new_zseries_recipe_save', methods=['POST'])
def new_zseries_recipe_save():
    recipe = request.get_json()
    recipe['id'] = increment_zseries_recipe_id()
    recipe['start_water'] = recipe.get('start_water', 13.1)
    filename = zseries_recipe_path().joinpath('{}.json'.format(recipe['name'].replace(' ', '_')))
    if not filename.exists():
        with open(filename, "w") as file:
            json.dump(recipe, file, indent=4, sort_keys=True)
        return '', 204
    else:
        return 'Recipe Exists!', 418


@main.route('/update_zseries_recipe', methods=['POST'])
def update_zseries_recipe():
    update_recipe = request.get_json()
    files = list(zseries_recipe_path().glob(file_glob_pattern))
    for filename in files:
        recipe = load_zseries_recipe(filename)
        if str(recipe.id) == update_recipe['id']:
            recipe.update_recipe(filename, update_recipe)
    return '', 204


@main.route('/device/<uid>/sessions/<session_type>', methods=['PUT'])
def update_device_session(uid, session_type):
    update = request.get_json()
    valid_session = True
    if session_type == 'ferm':
        session = active_ferm_sessions[uid]
    elif session_type == 'iSpindel':
        session = active_iSpindel_sessions[uid]
    else:
        valid_session = False

    if valid_session:
        if update['active'] == False:
            session.active = False
            if session.file != None:
                session.file.seek(0, os.SEEK_END)
                if session.file.tell() > 0:
                    # mark for completion and archive session file
                    session.file.seek(session.file.tell() - 1, os.SEEK_SET)  # Remove trailing comma from last data set
                    session.file.write('\n]')
                    session.cleanup()
                else:
                    # delete empty session file (user started fermentation, but device never reported data)
                    os.remove(session.filepath)
        else:
            session.active = True

        return '', 204
    else:
        current_app.logger.error(f'invalid session type : {session_type}')
        return 'Invalid session type provided \"' + session_type + '\"', 418


ALLOWED_EXTENSIONS = {'json'}


def allowed_extension(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def recipe_dirpath(machine_type):
    dirpath = None
    if machine_type == "picobrew" or machine_type == "pico":
        dirpath = pico_recipe_path()
    elif machine_type == "zymatic":
        dirpath = zymatic_recipe_path()
    elif machine_type == "zseries":
        dirpath = zseries_recipe_path()
    return dirpath


@main.route('/recipes/<machine_type>', methods=['POST'])
def upload_file(machine_type):
    # check if the post request has the file part
    if 'recipe' not in request.files:
        current_app.logger.error(f'invalid input : no file part')
        return 'No file part', 400
    file = request.files['recipe']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        current_app.logger.error(f'invalid input : no selected file')
        return 'no selected file', 400
    if file and allowed_extension(file.filename):
        filename = secure_filename(file.filename).replace(' ', '_')
        dirpath = recipe_dirpath(machine_type)
        if dirpath == None:
            current_app.logger.error(f'invalid input : unsupported machine_type {machine_type}')
            return 'unsupported machine_type', 400
        file.save(os.path.join(dirpath, filename))
        return f'upload of {file.filename} successful', 204
    else:
        return f'unsupported file : {file.filename}', 400


@main.route('/recipes/<machine_type>/<id>/<name>.json', methods=['GET'])
def download_recipe(machine_type, id, name):
    dirpath = recipe_dirpath(machine_type)
    if dirpath == None:
        current_app.logger.error(f'invalid machine_type : {machine_type}')
        return f'Invalid machine type provided "{machine_type}"', 418

    files = list(dirpath.glob(file_glob_pattern))
    
    for filename in files:
        recipe = None
        if machine_type == "picobrew":
            recipe = load_pico_recipe(filename)
        elif machine_type == "zymatic":
            recipe = load_zymatic_recipe(filename)
        elif machine_type == "zseries":
            recipe = load_zseries_recipe(filename)

        # just to be sure check recipe.id and recipe.name replacing spaces with underscores (expected file naming by server)
        if recipe and str(recipe.id) == str(id) and str(recipe.name).replace(" ", "_") == name:
            response = make_response(send_file(filename))
            # custom content-type will force a download vs rendering with window.location
            response.headers['Content-Type'] = 'application/octet-stream'
            return response

    return f'Download Recipe: Failed to find recipe id "{id}" with name "{name}"', 418


@main.route('/sessions/<session_type>/<filename>', methods=['GET'])
def download_session(session_type, filename):
    session_dirpath = ""
    if session_type == "brew":
        session_dirpath = brew_archive_sessions_path()
    elif session_type == "ferm":
        session_dirpath = ferm_archive_sessions_path()
    elif session_type == "iSpindel":
        session_dirpath = iSpindel_archive_sessions_path()
    else:
        return f'Invalid session type provided "{session_type}"', 418

    files = list(session_dirpath.glob(file_glob_pattern))
    filepath = session_dirpath.joinpath(filename)

    for f in files:
        if f.name == filename:
            response = make_response(send_file(filepath))
            # custom content-type will force a download vs rendering with window.location
            response.headers['Content-Type'] = 'application/octet-stream'
            return response
    return f'Download Session: Failed to find session with filename "{filename}"', 418


@main.route('/delete_zseries_recipe', methods=['GET', 'POST'])
def delete_zseries_recipe():
    recipe_id = request.get_json()
    files = list(zseries_recipe_path().glob(file_glob_pattern))
    for filename in files:
        recipe = load_zseries_recipe(filename)
        if str(recipe.id) == recipe_id:
            os.remove(filename)
            return '', 204
    return f'Delete Recipe: Failed to find recipe id "{recipe_id}"', 418


@main.route('/import_zseries_recipe', methods=['GET', 'POST'])
def import_zseries_recipe():
    if request.method == 'POST':
        data = request.get_json()
        uid = data['uid'] # machine productId
        try:
            import_recipes(uid, None, None, MachineType.ZSERIES)
            return '', 204
        except Exception as e:
            current_app.logger.error(f'import of recipes failed: {e}')
            return getattr(e, 'message', e.args[0]), 400
    else:
        machine_ids = [uid for uid in active_brew_sessions if active_brew_sessions[uid].machine_type == MachineType.ZSERIES]
        return render_template_with_defaults('import_brewhouse_recipe.html', user_required=False, machine_ids=machine_ids)


def load_zseries_recipes():
    files = list(zseries_recipe_path().glob(file_glob_pattern))
    recipes = [load_zseries_recipe(file) for file in files]
    return list(sorted(filter(lambda x: x.name != None, recipes), key=lambda x: x.name))


def load_zseries_recipe(file):
    recipe = ZSeriesRecipe()
    parse_recipe(MachineType.ZSERIES, recipe, file)
    recipe.name_escaped = escape(recipe.name).replace(" ", "_")
    return recipe


def parse_recipe(machineType, recipe, file):
    try:
        recipe.parse(file)
    except Exception as e:
        current_app.logger.error("ERROR: An exception occurred parsing recipe {}".format(file))
        current_app.logger.error(e)
        add_invalid_recipe(machineType, file)
    

def get_zseries_recipes():
    global zseries_recipes
    return zseries_recipes


def get_invalid_recipes():
    global invalid_recipes
    return invalid_recipes


def add_invalid_recipe(deviceType, file):
    global invalid_recipes
    if deviceType not in invalid_recipes:
        invalid_recipes[deviceType] = set()
    invalid_recipes.get(deviceType).add(file)


@main.route('/delete_file', methods=['POST'])
def delete_file():
    body = request.get_json()
    filename = body['filename']
    if body['type'] == "recipe":
        filepath = Path(filename)
        if filepath:
            os.remove(filename)
            for device in invalid_recipes:
                if filepath in invalid_recipes[device]:
                    invalid_recipes[device].remove(Path(filename))
            return '', 204
        current_app.logger.error("ERROR: failed to delete recipe file {}".format(filename))
        return "Delete Filename: Failed to find recipe file {}".format(filename), 418
    elif body['type'] in ['brew', 'ferm', 'iSpindel', 'still']:
        filepath = Path(filename)
        if filepath:
            os.remove(filename)
            if body['type'] in invalid_sessions and filepath in invalid_sessions[body['type']]:
                invalid_sessions[body['type']].remove(Path(filename))
            return '', 204
        current_app.logger.error("ERROR: failed to delete {} session file {}".format(body['type'], filename))
        return "Delete Filename: Failed to find {} session file".format(body['type'], filename), 418
    else:
        current_app.logger.error("ERROR: failed to delete {} as the file type {} was not supported".format(filename, body['type']))
    return 'Delete Filename: Unsupported file type specified {}'.format(body['type']), 418


@main.route('/pico_recipes')
def _pico_recipes():
    global pico_recipes, invalid_recipes
    pico_recipes = load_pico_recipes()
    recipes_dict = [json.loads(json.dumps(recipe, default=lambda r: r.__dict__)) for recipe in pico_recipes]
    return render_template_with_defaults('pico_recipes.html', recipes=recipes_dict, invalid=invalid_recipes.get(MachineType.PICOBREW, set()))


@main.route('/new_pico_recipe', methods=['GET', 'POST'])
def new_pico_recipe():
    if request.method == 'POST':
        recipe = request.get_json()
        recipe['id'] = uuid.uuid4().hex[:14]
        filename = pico_recipe_path().joinpath('{}.json'.format(recipe['name'].replace(' ', '_')))
        if not filename.exists():
            with open(filename, "w") as file:
                json.dump(recipe, file, indent=4, sort_keys=True)
            return '', 204
        else:
            return 'Recipe Exists!', 418
    else:
        return render_template_with_defaults('new_pico_recipe.html')


@main.route('/import_pico_recipe', methods=['GET', 'POST'])
def import_pico_recipe():
    if request.method == 'POST':
        data = request.get_json()
        rfid = data['rfid'] # picopak rfid
        uid = data['uid'] # picopak rfid
        try:
            # import for picobrew and picobrew_c are the same
            import_recipes(uid, None, rfid, MachineType.PICOBREW)
            return '', 204
        except Exception as e:
            current_app.logger.error(f'import of picopak recipe failed: {e}')
            return getattr(e, 'message', e.args[0]), 400
    else:
        machine_ids = [uid for uid in active_brew_sessions if active_brew_sessions[uid].machine_type in [MachineType.PICOBREW, MachineType.PICOBREW_C]]
        return render_template_with_defaults('import_brewhouse_recipe.html', rfid_required=True, machine_ids=machine_ids)


@main.route('/update_pico_recipe', methods=['POST'])
def update_pico_recipe():
    update_recipe = request.get_json()
    files = list(pico_recipe_path().glob(file_glob_pattern))
    for filename in files:
        recipe = load_pico_recipe(filename)
        if recipe.id == update_recipe['id']:
            recipe.update_recipe(filename, update_recipe)
    return '', 204


@main.route('/delete_pico_recipe', methods=['GET', 'POST'])
def delete_pico_recipe():
    recipe_id = request.get_json()
    files = list(pico_recipe_path().glob(file_glob_pattern))
    for filename in files:
        recipe = load_pico_recipe(filename)
        if recipe.id == recipe_id:
            os.remove(filename)
            return '', 204
    return 'Delete Recipe: Failed to find recipe id "{recipe_id}"', 418


def load_pico_recipes():
    files = list(pico_recipe_path().glob(file_glob_pattern))
    recipes = [load_pico_recipe(file) for file in files]
    return list(sorted(filter(lambda x: x.name != None, recipes), key=lambda x: x.name))


def load_pico_recipe(file):
    recipe = PicoBrewRecipe()
    parse_recipe(MachineType.PICOBREW, recipe, file)
    
    recipe.name_escaped = escape(recipe.name).replace(" ", "_")
    return recipe


def get_pico_recipes():
    global pico_recipes
    return pico_recipes


def parse_brew_session(file):
    try:
        return load_brew_session(file)
    except Exception as e:
        current_app.logger.error("An exception occurred parsing {}".format(file))
        current_app.logger.error(e)
        add_invalid_session("brew", file)


def get_invalid_sessions(sessionType):
    global invalid_sessions
    return invalid_sessions.get(sessionType, set())


def add_invalid_session(sessionType, file):
    global invalid_sessions
    if sessionType not in invalid_sessions:
        invalid_sessions[sessionType] = set()
    invalid_sessions.get(sessionType).add(file)


def load_active_brew_sessions():
    brew_sessions = []

    # process brew_sessions from memory
    for uid in active_brew_sessions:
        brew_sessions.append({'alias': active_brew_sessions[uid].alias,
                              'machine_type': active_brew_sessions[uid].machine_type,
                              'graph': get_brew_graph_data(uid, active_brew_sessions[uid].name,
                                                           active_brew_sessions[uid].step,
                                                           active_brew_sessions[uid].data,
                                                           active_brew_sessions[uid].is_pico)})
    return brew_sessions


def load_brew_sessions(uid=None):
    files = []
    if uid:
        files = list(brew_archive_sessions_path().glob("[^_.]*#{}*.json".format(uid)))
    else:
        files = list(brew_archive_sessions_path().glob(file_glob_pattern))
    brew_sessions = [parse_brew_session(file) for file in sorted(files, reverse=True)]
    return list(filter(lambda x: x != None, brew_sessions))


def parse_ferm_session(file):
    try:
        return load_ferm_session(file)
    except:
        current_app.logger.error("ERROR: An exception occurred parsing {}".format(file))
        add_invalid_session("ferm", file)
    

def load_active_ferm_sessions():
    ferm_sessions = []
    for uid in active_ferm_sessions:
        ferm_sessions.append({'alias': active_ferm_sessions[uid].alias,
                              'uid': uid,
                              'active': active_ferm_sessions[uid].active,
                              'graph': get_ferm_graph_data(uid, active_ferm_sessions[uid].voltage,
                                                           active_ferm_sessions[uid].data)})
    return ferm_sessions


def load_ferm_sessions():
    files = list(ferm_archive_sessions_path().glob(file_glob_pattern))
    ferm_sessions = [parse_ferm_session(file) for file in sorted(files, reverse=True)]
    return list(filter(lambda x: x != None, ferm_sessions))


def parse_iSpindel_session(file):
    try:
        return load_iSpindel_session(file)
    except:
        current_app.logger.error("ERROR: An exception occurred parsing {}".format(file))
        add_invalid_session("iSpindel", file)


def load_active_iSpindel_sessions():
    iSpindel_sessions = []
    for uid in active_iSpindel_sessions:
        iSpindel_sessions.append({'alias': active_iSpindel_sessions[uid].alias,
                                  'uid' : uid,
                                  'active': active_iSpindel_sessions[uid].active,
                                  'graph': get_iSpindel_graph_data(uid, active_iSpindel_sessions[uid].voltage,
                                                                   active_iSpindel_sessions[uid].data)})
    return iSpindel_sessions


def load_iSpindel_sessions():
    files = list(iSpindel_archive_sessions_path().glob(file_glob_pattern))
    iSpindel_sessions = [parse_iSpindel_session(file) for file in sorted(files, reverse=True)]
    return list(filter(lambda x: x != None, iSpindel_sessions))


# Read initial recipe list on load
pico_recipes = []
zymatic_recipes = []
zseries_recipes = []

brew_sessions = []
ferm_sessions = []

invalid_recipes = {}
invalid_sessions = {}


def initialize_data():
    global pico_recipes, zymatic_recipes, zseries_recipes, invalid_recipes
    global brew_sessions, ferm_sessions

    # Read initial recipe list on load
    pico_recipes = load_pico_recipes()
    zymatic_recipes = load_zymatic_recipes()
    zseries_recipes = load_zseries_recipes()

    # load all archive brew sessions
    brew_sessions = load_active_brew_sessions()
    ferm_sessions = load_active_ferm_sessions()
    iSpindel_sessions = load_active_iSpindel_sessions()


# utilities
def increment_zseries_recipe_id():
    recipe_id = 1
    found = False

    recipe_ids = [r.id for r in get_zseries_recipes()]
    while recipe_id in recipe_ids:
        recipe_id += 1

    return recipe_id
