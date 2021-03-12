from datetime import datetime
import time
import asyncio
from bleak import BleakScanner

from .routes_tilt_api import process_tilt_data

IBEACON_PROXIMITY_TYPE = b"\x02\x15"

TILTS = {
    'a495bb10c5b14b44b5121370f02d74de': 'Red',
    'a495bb20c5b14b44b5121370f02d74de': 'Green',
    'a495bb30c5b14b44b5121370f02d74de': 'Black',
    'a495bb40c5b14b44b5121370f02d74de': 'Purple',
    'a495bb50c5b14b44b5121370f02d74de': 'Orange',
    'a495bb60c5b14b44b5121370f02d74de': 'Blue',
    'a495bb70c5b14b44b5121370f02d74de': 'Yellow',
    'a495bb80c5b14b44b5121370f02d74de': 'Pink',
}

def get_number(data):
    integer = 0
    multiple = 256
    for c in data:
        integer += c * multiple
        multiple = 1
    return integer

def get_string(data):
    string = ''
    for c in data:
        string += '%02x' % c
    return string

# there may be a better way, but i wasn't sure how to filter out 
# other devices better than this. The name is currently always 'Tilt'
# but it seems like a bad idea to just trust that or it could just be
# if d.name.startswith('Tilt'):
def tilts(devices):
    tilts=[]
    for d in devices:
        if d.metadata['manufacturer_data'] and 76 in d.metadata['manufacturer_data']:
            data = d.metadata['manufacturer_data'][76]
            #print(get_string(data))
            if bytearray(data[:2]) == bytearray(IBEACON_PROXIMITY_TYPE):
                color_uid=get_string(data[2:18])
                if color_uid in TILTS:
                    # maintain same field names as pytilt in case someone wants to use that
                    # but add uid and rssi
                    uid = d.metadata['uuids'][0] if ('uuids' in d.metadata and len(d.metadata['uuids']) > 0) else d.address
                    tilts.append({
                        'uid': uid,
                        'rssi': get_number(data[-1:]),
                        'color': TILTS[color_uid],
                        'timestamp': datetime.now().isoformat(),
                        'temp': get_number(data[18:20]),    # fahrenheit
                        'gravity': get_number(data[20:22]), # gravity * 1000
                    })
    return tilts


async def scan(app):
    #print("Scanning for tilts...")
    with app.app_context():
        devices = await BleakScanner.discover(10.0)
        for tilt in tilts(devices):
            #print(tilt)
            process_tilt_data(tilt)


def run(app, sleep_interval):
    print ("Starting Tilt collection thread")

    try:
        while True:
            asyncio.run(scan(app))
            time.sleep(sleep_interval)
    except Exception as e:
        print(e)
        print("Error accessing bluetooth device. Shutting down Tilt thread...")
        return

    

