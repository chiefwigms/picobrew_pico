import json
import os
import re
import requests
import shlex
import socket
import subprocess
import sys
import traceback
import uuid
from ruamel.yaml import YAML
from flask import current_app, make_response, render_template, request, redirect, send_file
from pathlib import Path
from threading import Thread
from time import sleep
from os import path

from . import main
from .config import MachineType, base_path, server_config
from .model import PicoBrewSession, PicoFermSession, PicoStillSession, iSpindelSession, SupportObject
from .recipe_import import import_recipes
from .recipe_parser import PicoBrewRecipe, PicoBrewRecipeImport, ZymaticRecipe, ZymaticRecipeImport, ZSeriesRecipe
from .session_parser import load_iSpindel_session, get_iSpindel_graph_data, load_ferm_session, get_ferm_graph_data, get_brew_graph_data, load_brew_session, active_brew_sessions, active_ferm_sessions, active_iSpindel_sessions, active_still_sessions
from .config import base_path, zymatic_recipe_path, zseries_recipe_path, pico_recipe_path, ferm_archive_sessions_path, brew_archive_sessions_path, iSpindel_archive_sessions_path, MachineType


file_glob_pattern = "[!._]*.json"
yaml = YAML()


def system_info():
    try:
        system_info = subprocess.check_output("cat /etc/os-release || sw_vers || systeminfo | findstr /C:'OS'", shell=True)
        system_info = system_info.decode("utf-8")
    except:
        system_info = "Not Supported on this Device"

    return system_info


def platform():
    system = system_info()
    if 'raspbian' in system:
        return 'RaspberryPi'
    elif 'Mac OS X' in system:
        return 'MacOS'
    elif 'Microsoft Windows' in system:
        return 'Windows'
    else:
        return "unknown"


platform_info = platform()


def render_template_with_defaults(template, **kwargs):
    return render_template(template, platform=platform_info, **kwargs)


# -------- Routes --------
@main.route('/')
def index():
    return render_template_with_defaults('index.html', brew_sessions=load_active_brew_sessions(),
                           ferm_sessions=load_active_ferm_sessions(),
                           iSpindel_sessions=load_active_iSpindel_sessions())


@main.route('/restart_server')
def restart_server():
    # git pull & install any updated requirements
    os.system('cd {0}; git pull; pip3 install -r requirements.txt'.format(base_path()))
    # TODO: Close file handles for open sessions?

    def restart():
        sleep(2)
        os.execl(sys.executable, *([sys.executable]+sys.argv))
    thread = Thread(target=restart, daemon=True)
    thread.start()
    return redirect('/')


@main.route('/restart_system')
def restart_system():
    os.system('shutdown -r now')
    # TODO: redirect to a page with alert of restart
    return redirect('/')


@main.route('/shutdown_system')
def shutdown_system():
    os.system('shutdown -h now')
    # TODO: redirect to a page with alert of shutdown
    return redirect('/')


@main.route('/logs')
def view_logs():
    return render_template_with_defaults('logs.html')


@main.route('/logs/<log_type>.log')
def download_logs(log_type):
    try:
        filename = ""
        if log_type == 'nginx.access':
            filename = "/var/log/nginx/picobrew.access.log"
        elif log_type == 'nginx.error':
            filename = "/var/log/nginx/picobrew.error.log"
        elif log_type == 'picobrew_pico':
            max_lines = request.args.get('max', 20000)
            filename = f"{current_app.config['BASE_PATH']}/app/logs/picobrew_pico.log"
            subprocess.check_output(f"systemctl status rc.local -n {max_lines} > {filename}", shell=True)
        else:
            error_msg = f"invalid log type specified {log_type} is unsupported"
            return error_msg, 400

        response = make_response(send_file(filename))
        # custom content-type will force a download vs rendering with window.location
        response.headers['Content-Type'] = 'application/octet-stream'
        return response
    except Exception as e:
        error = f'Unexpected Error Retrieving {log_type} log file:<br/> {e}'
        return error, 500


@main.route('/devices', methods=['GET', 'POST'])
def handle_devices():
    active_sessions = {
        'brew': active_brew_sessions,
        'ferm': active_ferm_sessions,
        'iSpindel': active_iSpindel_sessions,
        'still': active_still_sessions
    }
    current_app.logger.debug(server_config())

    # register device alias and type
    if request.method == 'POST':
        mtype = MachineType(request.form['machine_type'])
        uid = request.form['uid']
        alias = request.form['alias']

        # verify uid not already configured
        if (uid in {**active_brew_sessions, **active_ferm_sessions, **active_iSpindel_sessions, **active_still_sessions} 
                and active_session(uid).alias != ''):
            error = f'Product ID {uid} already configured'
            current_app.logger.error(error)
            return render_template_with_defaults('devices.html', error=error,
                config=server_config(), active_sessions=active_sessions)

        current_app.logger.debug(f'machine_type: {mtype}; uid: {uid}; alias: {alias}')

        # add new device into config
        cfg_file = base_path().joinpath('config.yaml')
        with open(cfg_file, 'r') as f:
            server_cfg = yaml.load(f)
        try:
            new_server_cfg = server_cfg
            with open(cfg_file, 'w') as f:
                if new_server_cfg['aliases'][mtype] is None:
                    new_server_cfg['aliases'][mtype] = {}
                new_server_cfg['aliases'][mtype][uid] = alias
                yaml.dump(new_server_cfg, f)
                current_app.config.update(SERVER_CONFIG=server_cfg)
        except Exception as e:
            with open(cfg_file, 'w') as f:
                yaml.dump(server_cfg, f)
            error = f'Unexpected Error Writing Configuration File: {e}'
            current_app.logger.error(e)
            return render_template_with_defaults('devices.html', error=error,
                config=server_config(), active_sessions=active_sessions)

        # ... and into already loaded active sessions
        if mtype is MachineType.PICOFERM:
            if uid not in active_ferm_sessions:
                active_ferm_sessions[uid] = PicoFermSession()
            active_ferm_sessions[uid].alias = alias
        elif mtype is MachineType.PICOSTILL:
            if uid not in active_still_sessions:
                active_still_sessions[uid] = PicoStillSession()
            active_still_sessions[uid].alias = alias
        elif mtype is MachineType.ISPINDEL:
            if uid not in active_iSpindel_sessions:
                active_iSpindel_sessions[uid] = iSpindelSession()
            active_iSpindel_sessions[uid].alias = alias
        else:
            if uid not in active_brew_sessions:
                active_brew_sessions[uid] = PicoBrewSession(mtype)
            active_brew_sessions[uid].is_pico = True if mtype in [MachineType.PICOBREW, MachineType.PICOBREW_C] else False
            active_brew_sessions[uid].alias = alias

    return render_template_with_defaults('devices.html', config=server_config(), active_sessions=active_sessions)


@main.route('/devices/<uid>', methods=['POST', 'DELETE'])
def handle_specific_device(uid):
    active_sessions = {
        'brew': active_brew_sessions,
        'ferm': active_ferm_sessions,
        'iSpindel': active_iSpindel_sessions,
        'still': active_still_sessions
    }

    # updated already registered device alias
    mtype = MachineType(request.form['machine_type'])
    alias = request.form['alias'] if 'alias' in request.form else ''

    # verify uid is already configured
    if uid not in {**active_brew_sessions, **active_ferm_sessions, **active_iSpindel_sessions, **active_still_sessions}:
        error = f'Product ID {uid} not already configured'
        current_app.logger.error(error)
        return render_template_with_defaults('devices.html', error=error,
            config=server_config(), active_sessions=active_sessions)

    current_app.logger.debug(f'machine_type: {mtype}; uid: {uid}; alias: {alias}')

    # add new device into config
    cfg_file = base_path().joinpath('config.yaml')
    with open(cfg_file, 'r') as f:
        server_cfg = yaml.load(f)
    try:
        new_server_cfg = server_cfg
        with open(cfg_file, 'w') as f:
            if request.method == 'POST':
                new_server_cfg['aliases'][mtype][uid] = alias
            elif request.method == 'DELETE':
                del(new_server_cfg['aliases'][mtype][uid])
            yaml.dump(new_server_cfg, f)
            current_app.config.update(SERVER_CONFIG=server_cfg)
    except Exception as e:
        with open(cfg_file, 'w') as f:
            yaml.dump(server_cfg, f)
        error = f'Unexpected Error Writing Configuration File: {e}'
        current_app.logger.error(e)
        return render_template_with_defaults('devices.html', error=error,
            config=server_config(), active_sessions=active_sessions)

    # ... and change existing active session references to alias
    if mtype is MachineType.PICOFERM:    
        active_ferm_sessions[uid].alias = alias
    elif mtype is MachineType.PICOSTILL:
        active_still_sessions[uid].alias = alias
    elif mtype is MachineType.ISPINDEL:
        active_iSpindel_sessions[uid].alias = alias
    else:
        active_brew_sessions[uid].alias = alias

    if request.method == 'DELETE':
        return '', 204
    else:
        return redirect('/devices')


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
    update = request.get_json()
    files = list(zymatic_recipe_path().glob(file_glob_pattern))
    for filename in files:
        recipe = load_zymatic_recipe(filename)
        if recipe.id == update['id']:
            recipe.update_steps(filename, update['steps'])
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
    update = request.get_json()
    files = list(zseries_recipe_path().glob(file_glob_pattern))
    for filename in files:
        recipe = load_zseries_recipe(filename)
        if str(recipe.id) == update['id']:
            recipe.update_steps(filename, update['steps'])
    return '', 204


@main.route('/device/<uid>/sessions/<session_type>', methods=['PUT'])
def update_device_session(uid, session_type):
    update = request.get_json()
    if session_type == 'ferm':
        session = active_ferm_sessions[uid]

        if update['active'] == False:
            session.active = False
            if session.file != None:
                session.file.seek(0, os.SEEK_END)
                if session.file.tell() > 0:
                    # mark for completion and archive session file
                    session.file.seek(session.file.tell() - 1, os.SEEK_SET)  # Remove trailing , from last data set
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


@main.route('/recipes/<machine_type>/<rid>/<name>.json', methods=['GET'])
def download_recipe(machine_type, rid, name):
    recipe_dirpath = ""
    if machine_type == "picobrew":
        recipe_dirpath = pico_recipe_path()
    elif machine_type == "zymatic":
        recipe_dirpath = zymatic_recipe_path()
    elif machine_type == "zseries":
        recipe_dirpath = zseries_recipe_path()
    else:
        current_app.logger.error(f'invalid machine_type : {machine_type}')
        return 'Invalid machine type provided \"' + machine_type + '\"', 418

    files = list(recipe_dirpath.glob(file_glob_pattern))
    
    for filename in files:
        recipe = load_zseries_recipe(filename)
        if str(recipe.id) == str(rid) and str(recipe.name) == name:
            response = make_response(send_file(filename))
            # custom content-type will force a download vs rendering with window.location
            response.headers['Content-Type'] = 'application/octet-stream'
            return response
    return 'Download Recipe: Failed to find recipe id \"' + id + '\"', 418


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
        return 'Invalid session type provided \"' + session_type + '\"', 418

    files = list(session_dirpath.glob(file_glob_pattern))
    filepath = session_dirpath.joinpath(filename)

    for f in files:
        if f.name == filename:
            response = make_response(send_file(filepath))
            # custom content-type will force a download vs rendering with window.location
            response.headers['Content-Type'] = 'application/octet-stream'
            return response
    return 'Download Session: Failed to find session with filename \"' + filename + '\"', 418


@main.route('/delete_zseries_recipe', methods=['GET', 'POST'])
def delete_zseries_recipe():
    recipe_id = request.get_json()
    files = list(zseries_recipe_path().glob(file_glob_pattern))
    for filename in files:
        recipe = load_zseries_recipe(filename)
        if str(recipe.id) == recipe_id:
            os.remove(filename)
            return '', 204
    return 'Delete Recipe: Failed to find recipe id \"' + recipe_id + '\"', 418


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
    return recipe


def parse_recipe(machineType, recipe, file):
    try:
        recipe.parse(file)
    except:
        current_app.logger.error("ERROR: An exception occurred parsing recipe {}".format(file))
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
        recipe[
            'image'] = '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffe000ffc01ffffc0000000000000003fff0003f601ff7ff0000000000000000fe7c00dff003de7f8000800030000000ff3e000ff801ff7f80078001fe000000dfbe000ff801feff80070001fe0000009c37000de000dffc0007803ffe0000021c070001c000cbf80007803ffe000000dcbf800dc0002ff0000780ffff000000fc9f800fc0003fe00007a3ffff800003fc1f800fc0000dc00007ffffff000003fc3f801dc0000fc00007f1f8bf000002bcb7800dc0000dc00007f0f9fffc00003c278001c00021c00007f079ff0600023c0f8021c00021c00007fe10fe0200003c1f8001c00021c00007e000ff00000c1c3f00c1c000c1c00007e080ff00000000fe0080600000600007e010ff00000ffffc00fff000fff00007e001ff00000ffff800fff800fff80007e001ff000007ffe0007ff8003ff80007f000fe00000000000000000000000007f001fe00fffe03fff003fffcfffbff87f001fe001fffc0ffff03fffcffffffc7e0007e00cfff633c3f807e3e1cfdede7e0017e006fffb13f9fc03f9f3dfdefe7e0017e000ffff8bfefc03fdf3cffe7e7e0017e0007eef8b7ffe037df1cfdf787f0017e0001e6bc87a7e0073f18f8ff07f0017e0005cc3c841bf02fbf1aefff07f8dffe02070d7c3c3ff030df1e4ece07fdffff8c24067c303fe0ffe00e0e4e07fdffff003df778f79bc0ffe00f1f0e07fddffe010dff30bfcdf0afec0f1f0e07fc08ff7015fd38afedb82fce0f1e1e07fffffe0001e4388f21bc8f0f061e1c07fffffc0001e03c8f203c0f4f061e1c07e0017c0061f07f07003d078f063e1c07c0003e000000fe01987c000f033f1c03e0007c00ffffffffcfffffff03fff800ff9ff000fffffbffeffbffff03fbf800000000007fffe1ffe3f1ffff00f9f800000000001fff00ffc0c0fffe007070000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
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
    update = request.get_json()
    files = list(pico_recipe_path().glob(file_glob_pattern))
    for filename in files:
        recipe = load_pico_recipe(filename)
        if recipe.id == update['id']:
            recipe.update_steps(filename, update['steps'])
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
    return 'Delete Recipe: Failed to find recipe id \"' + recipe_id + '\"', 418


def available_networks():
    # TODO: properly handle failures by hiding settings in /setup or showing error

    wifi_list = subprocess.check_output('./scripts/pi/wifi_scan.sh | grep 2.4', shell=True)
    networks = []
    for network in wifi_list.split(b'\n'):
        network_parts = shlex.split(network.decode())
        if len(network_parts) == 6:
            networks.append({
                "bssid": network_parts[0],
                "ssid": network_parts[1],
                "frequency": network_parts[2],
                "channel": network_parts[3],
                "signal": network_parts[4],
                "encryption": network_parts[5]
            })
    return networks


@main.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        payload = request.get_json()

        if 'hostname' in payload:
            # change the device hostname and reboot
            new_hostname = payload['hostname']

            # check if hostname is only a-z0-9\-
            if not re.match("^[a-zA-Z0-9-]+$", new_hostname):
                current_app.logger.error("ERROR: invalid hostname provided: {}".format(new_hostname))
                return 'Invalid Hostname (only supports a-z 0-9 and - as characters)!', 400

            subprocess.check_output(
                """echo '{}' > /etc/hostname""".format(new_hostname), shell=True)
            subprocess.check_output(
                """sed -i -e 's/{}/{}/' /etc/hosts""".format(hostname(), new_hostname), shell=True)

            # restart for new host settings to take effect
            os.system('shutdown -r now')

            return '', 204
        elif 'interface' in payload:
            if payload['interface'] == 'wlan0':
                # change wireless configuration (wpa_supplicant-wlan0.conf and wpa_supplicant.conf)
                # sudo sed -i -e"s/^\bssid=.*/ssid=\"$SSID\"/" /etc/wpa_supplicant/wpa_supplicant.conf
                # sudo sed -i -e"s/^psk=.*/psk=\"$WIFIPASS\"/" /etc/wpa_supplicant/wpa_supplicant.conf

                try:
                    # <= beta4 => /etc/wpa_supplicant/wpa_supplicant.conf
                    # >= beta5 => /etc/wpa_supplicant/wpa_supplicant-wlan0.conf
                    wpa_files = " ".join([_x for _x in ("/etc/wpa_supplicant/wpa_supplicant.conf", "/etc/wpa_supplicant/wpa_supplicant-wlan0.conf") if os.path.exists(_x)])

                    # set ssid in wpa_supplicant files
                    # regex \b marks a word boundary
                    ssid = payload['ssid']
                    subprocess.check_output(
                        """sed -i 's/\\bssid=.*/ssid="{}"/' {}""".format(ssid, wpa_files), shell=True)

                    # set bssid (if set by user) in wpa_supplicant files
                    if 'bssid' in payload and payload['bssid']:
                        bssid = payload['bssid']
                        # remove comment for bssid line (if present)
                        subprocess.check_output(
                            """sudo sed -i '/bssid/s/# *//g' {}""".format(wpa_files), shell=True)
                        subprocess.check_output(
                            """sudo sed -i 's/bssid=.*/bssid={}/' {}""".format(bssid, wpa_files), shell=True)
                    else:
                        # add a comment for bssid line (if present)
                        subprocess.check_output(
                            """sudo sed -i 's/\(bssid=.*\)/# \\1/g' {}""".format(wpa_files), shell=True)

                    # set credentials (if set by user) in wpa_supplicant files
                    if 'password' in payload:
                        psk = payload['password']
                        subprocess.check_output(
                            """sed -i 's/psk=.*/psk="{}"/' {}""".format(psk, wpa_files), shell=True)

                    def restart_wireless():
                        import subprocess
                        import time
                        time.sleep(2)
                        subprocess.check_output('systemctl restart wpa_supplicant@wlan0.service', shell=True)

                    # async restart wireless service
                    thread = Thread(target=restart_wireless)
                    current_app.logger.info("applying changes and restarting wireless interface")
                    thread.start()

                    return '', 204
                    # TODO: redirect to a page with alert of success or failure of wireless service reset
                except Exception:
                    current_app.logger.error("ERROR: error occured in wireless setup:", sys.exc_info()[2])
                    current_app.logger.error(traceback.format_exc())
                    return 'Wireless Setup Failed!', 418
            elif payload['interface'] == 'ap0':
                try:
                    hostapd_file = "/etc/hostapd/hostapd.conf"

                    # set ssid in hostapd file
                    ssid = payload['ssid']
                    subprocess.check_output(
                        """sed -i -e 's/ssid=.*/ssid={}/' {}""".format(ssid, hostapd_file), shell=True)

                    # set credentials (if set by user) in hostapd file
                    if 'password' in payload and payload['password']:
                        psk = payload['password']
                        subprocess.check_output(
                            """sed -i -e 's/wpa_passphrase=.*/wpa_passphrase={}/' {}""".format(psk, hostapd_file), shell=True)

                    def restart_ap0_interface():
                        import subprocess
                        import time
                        time.sleep(2)
                        subprocess.check_output('systemctl restart hostapd.service', shell=True)

                    # async restart hostapd service
                    thread = Thread(target=restart_ap0_interface)
                    thread.start()

                    return '', 204
                except Exception:
                    current_app.logger.error("ERROR: error occured in wireless setup:", sys.exc_info()[2])
                    current_app.logger.error(traceback.format_exc())
                    return 'Wireless Setup Failed!', 418
            else:
                current_app.logger.error("ERROR: invalid interface provided %s".format(payload['interface']))
                return 'Invalid Interface Provided - Setup Failed!', 418
        else:
            current_app.logger.error("ERROR: unsupported payload received %s".format(payload))
            return 'Invalid Setup Payload Received - Setup Failed!', 418
    else:
        return render_template_with_defaults('setup.html',
            hostname=hostname(),
            ap0=accesspoint_credentials(),
            wireless_credentials=wireless_credentials(),
            available_networks=available_networks())


def hostname():
    try:
        subprocess.check_output("more /etc/hostname", shell=True)
        return subprocess.check_output("hostname", shell=True).decode("utf-8").strip()
    except:
        current_app.logger.warn("WARN: current device doesn't support hostname changes")

    return None


def accesspoint_credentials():
    # TODO: properly handle No such file or directory by hiding settings in /setup or showing error
    try:
        ssid = subprocess.check_output('more /etc/hostapd/hostapd.conf | grep -w ^ssid | awk -F "=" \'{print $2}\'', shell=True)
        psk = subprocess.check_output('more /etc/hostapd/hostapd.conf | grep -w ^wpa_passphrase | awk -F "=" \'{print $2}\'', shell=True)
        
        return {
            'ssid': ssid.decode("utf-8").strip().strip('"'),
            'psk': psk.decode("utf-8").strip().strip('"'),
        }
    except:
        current_app.logger.warn("WARN: failed to retrieve access point information from hostapd")
        
    return {}


def wireless_credentials():
    # TODO: properly handle No such file or directory by hiding settings in /setup or showing error

    # grep -w matches an exact word:
    #   example non match:
    #       echo "bssid=test-value" | grep -w ssid => ""
    #   example match:
    #       echo "bssid=test-value" | grep -w bssid => "bssid=test-value"
    cmd_template = "more /etc/wpa_supplicant/wpa_supplicant-wlan0.conf | grep -v '^\s*[#]' | grep -w {key} "

    ssid = subprocess.check_output(cmd_template.format(key='ssid') + '| awk -F "=" \'{print $2}\'', shell=True)
    psk = subprocess.check_output(cmd_template.format(key='psk') + '| awk -F "=" \'{print $2}\'', shell=True)

    try:
        # first remove any line that might be a comment (default)
        # second filter to the line that contains the text 'bssid'
        # return the value after the '=' in bssid=<value>
        bssid = subprocess.check_output(cmd_template.format(key='bssid') + '| awk -F "=" \'{print $2}\'', shell=True)
    except:
        bssid = None

    return { 
        'ssid': ssid.decode("utf-8").strip().strip('"'),
        'psk': psk.decode("utf-8").strip().strip('"'),
        'bssid': bssid.decode("utf-8").strip().strip('"')
    }


@main.route('/about', methods=['GET'])
def about():
    # query local git short sha
    gitSha = subprocess.check_output("cd {0}; git rev-parse --short HEAD".format(base_path()), shell=True)
    gitSha = gitSha.decode("utf-8")

    # query latest git remote sha
    try:
        latestMasterSha = subprocess.check_output("cd {0}; git fetch origin && git rev-parse --short origin/master".format(base_path()), shell=True)
        latestMasterSha = latestMasterSha.decode("utf-8")
    except:
        latestMasterSha = "unavailable (check network)"

    # query for local file changes
    try:
        localChanges = subprocess.check_output("cd {0}; git fetch origin; git --no-pager diff --name-only".format(base_path()), shell=True)
        localChanges = localChanges.decode("utf-8").strip()
    except:
        localChanges = "unavailable (check network)"

    # # capture raspbian pinout
    # proc = subprocess.Popen(["pinout"], stdout=subprocess.PIPE, shell=True)
    # (pinout, err) = proc.communicate()
    try:
        pinout = subprocess.check_output("pinout", shell=True)
        pinout = pinout.decode("utf-8")
    except:
        pinout = None

    image_release = os.environ.get("IMG_RELEASE", None)
    image_variant = os.environ.get("IMG_VARIANT", None)
    image_version = None if image_release == None else f"{image_release}_{image_variant}" 
    
    return render_template_with_defaults('about.html', git_version=gitSha, latest_git_sha=latestMasterSha, local_changes=localChanges,
                           os_release=system_info(), raspberrypi_info=pinout, raspberrypi_image=image_version)


def load_pico_recipes():
    files = list(pico_recipe_path().glob(file_glob_pattern))
    recipes = [load_pico_recipe(file) for file in files]
    return list(sorted(filter(lambda x: x.name != None, recipes), key=lambda x: x.name))


def load_pico_recipe(file):
    recipe = PicoBrewRecipe()
    parse_recipe(MachineType.PICOBREW, recipe, file)
    return recipe


def get_pico_recipes():
    global pico_recipes
    return pico_recipes


def parse_brew_session(file):
    try:
        return load_brew_session(file)
    except:
        current_app.logger.error("ERROR: An exception occurred parsing {}".format(file))
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


def active_session(uid):
    if uid in active_brew_sessions:
        return active_brew_sessions[uid]
    elif uid in active_ferm_sessions:
        return active_ferm_sessions[uid]
    elif uid in active_iSpindel_sessions:
        return active_iSpindel_sessions[uid]
    elif uid in active_still_sessions:
        return active_still_sessions[uid]
    
    return None
