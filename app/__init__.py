from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from pathlib import Path
from shutil import copyfile
from ruamel.yaml import YAML
import pathlib
from threading import Thread

BASE_PATH = Path(__file__).parents[1]

socketio = SocketIO()
yaml = YAML()

def create_dir(dir_path):
    # create the directory and any missing parent directories, if it doesn't already exist
    pathlib.Path(dir_path).mkdir(parents=True, exist_ok=True)


def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__)
    CORS(app)

    socketio.cors_allowed_origins = "*"
    socketio.init_app(app)

    # these imports required to be after socketio initialization
    from .main.config import MachineType
    from .main.model import PicoBrewSession, PicoFermSession, PicoStillSession, iSpindelSession, TiltSession
    from .main.routes_frontend import initialize_data
    from .main.session_parser import (restore_active_sessions, active_brew_sessions,
                                      active_ferm_sessions, active_still_sessions,
                                      active_iSpindel_sessions, active_tilt_sessions)

    from .main import main as main_blueprint
    from .main import tilt

    # ----- Routes ----------
    app.register_blueprint(main_blueprint)

    server_cfg = {}
    cfg_file = BASE_PATH.joinpath('config.yaml')
    if not pathlib.Path(cfg_file).exists():
        # copy config.example.yaml > config.yaml if config.yaml doesn't exist
        example_cfg_file = BASE_PATH.joinpath('config.example.yaml')
        copyfile(example_cfg_file, cfg_file)

    with open(cfg_file, 'r') as f:
        server_cfg = yaml.load(f)

    app.config.update(
        SECRET_KEY='bosco',
        CORS_HEADERS='Content-Type',
        BASE_PATH=BASE_PATH,
        RECIPES_PATH=BASE_PATH.joinpath('app/recipes'),
        SESSIONS_PATH=BASE_PATH.joinpath('app/sessions'),
        FIRMWARE_PATH=BASE_PATH.joinpath('app/firmware'),
        SERVER_CONFIG=server_cfg
    )

    # create subdirectories if they don't already exist
    create_dir(app.config['RECIPES_PATH'].joinpath('pico'))
    create_dir(app.config['RECIPES_PATH'].joinpath('zymatic'))
    create_dir(app.config['SESSIONS_PATH'].joinpath('brew/active'))
    create_dir(app.config['SESSIONS_PATH'].joinpath('brew/archive'))
    create_dir(app.config['SESSIONS_PATH'].joinpath('ferm/active'))
    create_dir(app.config['SESSIONS_PATH'].joinpath('ferm/archive'))
    create_dir(app.config['SESSIONS_PATH'].joinpath('iSpindel/active'))
    create_dir(app.config['SESSIONS_PATH'].joinpath('iSpindel/archive'))
    create_dir(app.config['SESSIONS_PATH'].joinpath('tilt/active'))
    create_dir(app.config['SESSIONS_PATH'].joinpath('tilt/archive'))

    with app.app_context():
        restore_active_sessions()
        initialize_data()

    if 'aliases' in server_cfg:
        machine_types = [MachineType.ZSERIES, MachineType.ZYMATIC, MachineType.PICOBREW,
                         MachineType.PICOBREW_C, MachineType.PICOFERM, MachineType.ISPINDEL,MachineType.TILT]
        for mtype in machine_types:
            aliases = server_cfg['aliases']
            if mtype in aliases and aliases[mtype] is not None:
                for uid in aliases[mtype]:
                    if uid in aliases[mtype] and uid != "uid":
                        if mtype == MachineType.PICOFERM:
                            if uid not in active_ferm_sessions:
                                active_ferm_sessions[uid] = PicoFermSession()
                            active_ferm_sessions[uid].alias = aliases[mtype][uid]
                        elif mtype == MachineType.ISPINDEL:
                            if uid not in active_iSpindel_sessions:
                                active_iSpindel_sessions[uid] = iSpindelSession()
                            active_iSpindel_sessions[uid].alias = aliases[mtype][uid]
                        elif mtype == MachineType.TILT:
                            if uid not in active_tilt_sessions:
                                active_tilt_sessions[uid] = TiltSession()
                            active_tilt_sessions[uid].alias = aliases[mtype][uid]
                        elif mtype == MachineType.PICOSTILL:
                            if uid not in active_still_sessions:
                                active_still_sessions[uid] = PicoStillSession()
                            active_still_sessions[uid].alias = aliases[mtype][uid]
                        else:
                            if uid not in active_brew_sessions:
                                active_brew_sessions[uid] = PicoBrewSession(mtype)
                            active_brew_sessions[uid].alias = aliases[mtype][uid]
                            active_brew_sessions[uid].machine_type = mtype
                            active_brew_sessions[uid].is_pico = True if mtype in [MachineType.PICOBREW, MachineType.PICOBREW_C] else False

    if server_cfg['tilt_monitoring']:
        sleep_interval = int(server_cfg['tilt_monitoring_interval']) if 'tilt_monitoring_interval' in server_cfg else 10
        tiltThread = Thread(name='Tilt', target=tilt.run, daemon=True, args=(app,sleep_interval))
        tiltThread.start()

    return app
