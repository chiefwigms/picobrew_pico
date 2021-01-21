from flask import Blueprint

main = Blueprint('main', __name__)

# required to load the API routes
from . import (routes_frontend, routes_server, routes_devices, routes_support, 
                routes_pico_api, routes_zymatic_api, routes_zseries_api, 
                routes_picoferm_api, routes_picostill_api, routes_iSpindel_api)
