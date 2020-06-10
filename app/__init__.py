from flask import *
from flask_cors import CORS
from flask_socketio import SocketIO
import json
from pathlib import Path
import shutil

ZYMATIC_RECIPE_PATH = 'app/recipes/zymatic'
PICO_RECIPE_PATH = 'app/recipes/pico'
BREW_ACTIVE_PATH = 'app/sessions/brew/active'
BREW_ARCHIVE_PATH = 'app/sessions/brew/archive'
FERM_ACTIVE_PATH = 'app/sessions/ferm/active'
FERM_ARCHIVE_PATH = 'app/sessions/ferm/archive'

ZYMATIC_LOCATION = {
    "PassThru": "0",
    "Mash": "1",
    "Adjunct1": "2",
    "Adjunct2": "3",
    "Adjunct3": "4",
    "Adjunct4": "5",
    "Pause": "6",
}
PICO_LOCATION = {
    "Prime": "0",
    "Mash": "1",
    "PassThru": "2",
    "Adjunct1": "3",
    "Adjunct2": "4",
    "Adjunct3": "6",
    "Adjunct4": "5",
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
        self.name = 'Waiting To Brew'
        self.step = ''
        self.session = ''
        self.recovery = ''
        self.is_pico = True
        self.data = []

    def cleanup(self):
        if self.file and self.filepath:
            self.file.close()
            shutil.move(str(self.filepath), str(Path(BREW_ARCHIVE_PATH)))
        self.file = None
        self.filepath = None
        self.name = 'Waiting To Brew'
        self.step = ''
        self.session = ''
        self.recovery = ''
        self.data = []


active_ferm_sessions = {}


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
    with open('aliases.json', 'r') as f:
        aliases = json.load(f, strict=False)
        if "Zymatic" in aliases:
            for uid in aliases["Zymatic"]:
                if uid != "uid":
                    active_brew_sessions[uid] = PicoBrewSession()
                    active_brew_sessions[uid].alias = aliases["Zymatic"][uid]
                    active_brew_sessions[uid].is_pico = False
                    # todo: if anything in active folder, load data in since the server probably crashed?
        if "PicoBrew" in aliases:
            for uid in aliases["PicoBrew"]:
                if uid != "uid":
                    active_brew_sessions[uid] = PicoBrewSession()
                    active_brew_sessions[uid].alias = aliases["PicoBrew"][uid]
                    # todo: if anything in active folder, load data in since the server probably crashed?
        if "PicoFerm" in aliases:
            for uid in aliases["PicoFerm"]:
                if uid != "uid":
                    active_ferm_sessions[uid] = PicoFermSession()
                    active_ferm_sessions[uid].alias = aliases["PicoFerm"][uid]
                    # todo: if anything in active folder, load data in since the server probably crashed?
    return app
