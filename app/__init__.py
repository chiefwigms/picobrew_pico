from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from pathlib import Path
from shutil import copyfile
import yaml
import pathlib

BASE_PATH = Path(__file__).parents[1]

socketio = SocketIO()

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
    from .main.model import PicoFermSession, PicoBrewSession
    from .main.routes_frontend import initialize_data
    from .main.session_parser import restore_active_sessions, active_brew_sessions, active_ferm_sessions

    from .main import main as main_blueprint

    # ----- Routes ----------
    app.register_blueprint(main_blueprint)

    server_cfg = {}
    cfg_file = BASE_PATH.joinpath('config.yaml')
    if not pathlib.Path(cfg_file).exists():
        # copy config.example.yaml -> config.yaml if config.yaml doesn't exist
        example_cfg_file = BASE_PATH.joinpath('config.example.yaml')
        copyfile(example_cfg_file, cfg_file)
    
    with open(cfg_file, 'r') as f:
        server_cfg = yaml.safe_load(f)

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

    with app.app_context():
        restore_active_sessions()
        initialize_data()
    if 'aliases' in server_cfg:
        machine_types = [MachineType.ZSERIES, MachineType.ZYMATIC, MachineType.PICOBREW, MachineType.PICOFERM, MachineType.PICOSTILL]
        for mtype in machine_types:
            aliases = server_cfg['aliases']
            if mtype in aliases and aliases[mtype] is not None:
                for uid in aliases[mtype]:
                    if uid in aliases[mtype] and uid != "uid":
                        if mtype == MachineType.PICOFERM:
                            active_ferm_sessions[uid] = PicoFermSession()
                            active_ferm_sessions[uid].alias = aliases[mtype][uid]
                        else:
                            active_brew_sessions[uid] = PicoBrewSession()
                            active_brew_sessions[uid].alias = aliases[mtype][uid]
                            active_brew_sessions[uid].is_pico = True if mtype == MachineType.PICOBREW else False

    return app
