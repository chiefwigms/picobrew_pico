from flask import Blueprint
main = Blueprint('main', __name__)
from . import routes_frontend, routes_api