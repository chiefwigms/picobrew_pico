from flask import Blueprint
main = Blueprint('main', __name__)
from . import routes_frontend, routes_pico_api, routes_picoferm_api
