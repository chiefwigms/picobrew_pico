from flask import *
from flask_cors import CORS
from flask_socketio import SocketIO

RECIPE_PATH = 'app/recipes'
SESSION_PATH = 'app/sessions'
PICO_LOCATION = {
    "Prime" : "0",
    "Mash" : "1",
    "PassThru" : "2",
    "Adjunct1" : "3",
    "Adjunct2" : "4",
    "Adjunct3" : "6",
    "Adjunct4" : "5",
}

class PicoSession():
    uid = ''
    name = 'Waiting to Brew'
    step = 'Brew Something!'
    filename = ''
    file = None
    data = []

current_session = PicoSession()
socketio = SocketIO()

def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__)
    CORS(app)
    app.config.update(CORS_HEADERS = 'Content-Type')

    from .main import main as main_blueprint

    # ----- Routes ----------
    app.register_blueprint(main_blueprint)
    socketio.init_app(app)
    return app
