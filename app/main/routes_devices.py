from ruamel.yaml import YAML
from flask import current_app, request, redirect
from pathlib import Path
from os import path

from . import main
from .frontend_common import active_session, render_template_with_defaults
from .model import PicoBrewSession, PicoFermSession, PicoStillSession, iSpindelSession
from .session_parser import (active_brew_sessions, active_ferm_sessions, 
                                active_iSpindel_sessions, active_still_sessions)
from .config import (base_path, server_config, MachineType,
                        zymatic_recipe_path, zseries_recipe_path, pico_recipe_path,
                        ferm_archive_sessions_path, brew_archive_sessions_path, iSpindel_archive_sessions_path)


yaml = YAML()


# -------- Routes --------
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
        uid = str(request.form['uid']).strip()
        alias = str(request.form['alias']).strip()

        # uid and alias are required
        if len(uid) == 0 or len(alias) == 0:
            if len(uid) == 0 and len(alias) == 0:
                error = f'Machine/Product ID and Alias are required'
            elif len(uid) == 0:
                error = f'Machine/Product ID is required'
            else:
                error = f'Alias is required'
            current_app.logger.error(error)
            return render_template_with_defaults('devices.html', error=error,
                config=server_config(), active_sessions=active_sessions)

        # uid and alias are required
        if len(uid) == 0 or len(alias) == 0:
            if len(uid) == 0 and len(alias) == 0:
                error = f'Machine/Product ID and Alias are required'
            elif len(uid) == 0:
                error = f'Machine/Product ID is required'
            else:
                error = f'Alias is required'
            current_app.logger.error(error)
            return render_template_with_defaults('devices.html', error=error,
                config=server_config(), active_sessions=active_sessions)

        # uid and alias are required
        if len(uid) == 0 or len(alias) == 0:
            if len(uid) == 0 and len(alias) == 0:
                error = f'Machine/Product ID and Alias are required'
            elif len(uid) == 0:
                error = f'Machine/Product ID is required'
            else:
                error = f'Alias is required'
            current_app.logger.error(error)
            return render_template_with_defaults('devices.html', error=error,
                config=server_config(), active_sessions=active_sessions)

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


