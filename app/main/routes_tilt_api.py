from webargs import fields
from webargs.flaskparser import use_args, FlaskParser
from marshmallow import INCLUDE, Schema

from . import main
from .tilt import process_tilt_data
from .units import convert_temp


arg_parser = FlaskParser()

# This supports using pytilt to get the data from the tilt using bluetooth and send via this API call
# See https://github.com/atlefren/pytilt but all you have to do is set the environment variable
#   PYTILT_URL=<your picobrew_pico server>/API/tilt
# and it will work without modifications

class TiltSchema(Schema):
    color = fields.Str(required=True),     # device ID
    temp = fields.Float(required=True),    # device temperature in Celcius
    gravity = fields.Int(required=True),   # calculated specific gravity
    timestamp = fields.Str(required=True), # time sample taken in ISO format e.g '2021-03-06T16:25:42.823122'

# Process tilt Data: /API/tilt
@main.route('/API/tilt', methods=['POST'])
@use_args(TiltSchema(many=True), unknown=INCLUDE)
def process_tilt_dataset(dataset):
    for data in dataset:
        data['temp'] = convert_temp(data['temp'], 'F')
        process_tilt_data(data)
    return('', 200)
