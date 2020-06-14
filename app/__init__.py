from flask import *
from flask_cors import CORS
from flask_socketio import SocketIO
from pathlib import Path
import shutil
import yaml

BASE_PATH = Path(__file__).parents[1]

# recipe paths
ZYMATIC_RECIPE_PATH = str(BASE_PATH.joinpath('app/recipes/zymatic'))
ZSERIES_RECIPE_PATH = str(BASE_PATH.joinpath('app/recipes/zseries'))
PICO_RECIPE_PATH = str(BASE_PATH.joinpath('app/recipes/pico'))

# sessions paths
BREW_ACTIVE_PATH = str(BASE_PATH.joinpath('app/sessions/brew/active'))
BREW_ARCHIVE_PATH = str(BASE_PATH.joinpath('app/sessions/brew/archive'))
FERM_ACTIVE_PATH = str(BASE_PATH.joinpath('app/sessions/ferm/active'))
FERM_ARCHIVE_PATH = str(BASE_PATH.joinpath('app/sessions/ferm/archive'))

ZYMATIC_LOCATION = {
    'PassThru': '0',
    'Mash': '1',
    'Adjunct1': '2',
    'Adjunct2': '3',
    'Adjunct3': '4',
    'Adjunct4': '5',
    'Pause': '6',
}

ZSERIES_LOCATION = {
    'PassThru': '0',
    'Mash': '1',
    'Adjunct1': '2',
    'Adjunct2': '3',
    'Adjunct3': '4',
    'Adjunct4': '5',
    'Pause': '6',
}

PICO_LOCATION = {
    'Prime': '0',
    'Mash': '1',
    'PassThru': '2',
    'Adjunct1': '3',
    'Adjunct2': '4',
    'Adjunct3': '6',
    'Adjunct4': '5',
}
PICO_SESSION = {
    0: 'Brewing',
    1: 'Deep Clean',
    2: 'Sous Vide',
    4: 'Cold Brew',
    5: 'Manual Brew',
}


active_brew_sessions = {}


class PicoBrewSession():
    def __init__(self):
        self.file = None
        self.filepath = None
        self.alias = ''
        self.created_at = None
        self.name = 'Waiting To Brew'
        self.type = 0
        self.step = ''
        self.session = ''   # session guid
        self.id = -1        # session id (interger)
        self.recovery = ''
        self.remaining_time = None
        self.is_pico = True
        self.data = []

    def cleanup(self):
        if self.file and self.filepath:
            self.file.close()
            shutil.move(str(self.filepath), str(Path(BREW_ARCHIVE_PATH)))
        self.file = None
        self.filepath = None
        self.created_at = None
        self.name = 'Waiting To Brew'
        self.type = 0
        self.step = ''
        self.session = ''
        self.id = -1
        self.recovery = ''
        self.remaining_time = None
        self.data = []


active_ferm_sessions = {}


server_cfg = {}


class PicoFermSession():
    def __init__(self):
        self.file = None
        self.filepath = None
        self.alias = ''
        self.uninit = True
        self.voltage = '-'
        self.start_time = None
        self.data = []

    def cleanup(self):
        if self.file and self.filepath:
            self.file.close()
            shutil.move(str(self.filepath), str(Path(FERM_ARCHIVE_PATH)))
        self.file = None
        self.filepath = None
        self.uninit = True
        self.voltage = '-'
        self.start_time = None
        self.data = []


socketio = SocketIO()


def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__)
    CORS(app)
    app.config.update(SECRET_KEY='bosco', CORS_HEADERS='Content-Type')

    from .main import main as main_blueprint

    # ----- Routes ----------
    app.register_blueprint(main_blueprint)
    socketio.init_app(app)
    cfg_file = BASE_PATH.joinpath('config.yaml')
    with open(cfg_file, 'r') as f:
        server_cfg = yaml.safe_load(f)

    if 'aliases' in server_cfg:
        machine_types = ["ZSeries", "Zymatic", "PicoBrew", "PicoFerm"]
        for mtype in machine_types:
            aliases = server_cfg['aliases']
            if mtype in aliases and aliases[mtype] != None:
                for uid in aliases[mtype]:
                    if uid in aliases[mtype] and uid != "uid":
                        if mtype == "PicoFerm":
                            active_ferm_sessions[uid] = PicoFermSession()
                        else:
                            active_brew_sessions[uid] = PicoBrewSession()
                            active_brew_sessions[uid].is_pico = True if mtype == "PicoBrew" else False

                        # todo: if anything in active folder, load data in since the server probably crashed?
                        active_ferm_sessions[uid].alias = aliases[mtype][uid]

    return app
