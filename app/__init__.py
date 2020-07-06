from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from pathlib import Path
import yaml

BASE_PATH = Path(__file__).parents[1]

server_cfg = {}

socketio = SocketIO()


def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__)
    CORS(app)

    socketio.cors_allowed_origins = "*"
    socketio.init_app(app)

    # these imports required to be after socketio initialization
    from .main.model import PicoFermSession, PicoBrewSession
    from .main.routes_frontend import initialize_data
    from .main.session_parser import restore_active_sessions, active_brew_sessions, active_ferm_sessions

    from .main import main as main_blueprint

    # ----- Routes ----------
    app.register_blueprint(main_blueprint)

    cfg_file = BASE_PATH.joinpath('config.yaml')
    with open(cfg_file, 'r') as f:
        server_cfg = yaml.safe_load(f)

    app.config.update(
        SECRET_KEY='bosco',
        CORS_HEADERS='Content-Type',
        BASE_PATH=BASE_PATH,
        RECIPES_PATH=BASE_PATH.joinpath('app/recipes'),
        SESSIONS_PATH=BASE_PATH.joinpath('app/sessions'),
        FIRMWARE_PATH=BASE_PATH.joinpath('app/firmware')
    )

    with app.app_context():
        restore_active_sessions()
        initialize_data()

    if 'aliases' in server_cfg:
        machine_types = ["ZSeries", "Zymatic", "PicoBrew", "PicoFerm"]
        for mtype in machine_types:
            aliases = server_cfg['aliases']
            if mtype in aliases and aliases[mtype] is not None:
                for uid in aliases[mtype]:
                    if uid in aliases[mtype] and uid != "uid":
                        if mtype == "PicoFerm":
                            active_ferm_sessions[uid] = PicoFermSession()
                            active_ferm_sessions[uid].alias = aliases[mtype][uid]
                        else:
                            active_brew_sessions[uid] = PicoBrewSession()
                            active_brew_sessions[uid].alias = aliases[mtype][uid]
                            active_brew_sessions[uid].is_pico = True if mtype == "PicoBrew" else False

    return app
