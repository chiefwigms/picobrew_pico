from datetime import datetime
import time
import bluetooth._bluetooth as bluez

from . import blescan
from .routes_tilt_api import process_tilt_data

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

def run(app, sleep_interval):
    dev_id = 0
    try:
        socket = bluez.hci_open_dev(dev_id)
        print ("Starting Tilt collection thread")
    except Exception as e:
        print(e)
        print("Error accessing bluetooth device. Shutting down Tilt thread...")
        return

    blescan.hci_le_set_scan_parameters(socket)
    blescan.hci_enable_le_scan(socket)

    while True:
        beacons = distinct(blescan.parse_events(socket, 10))
        with app.app_context():
            for beacon in beacons:
                if beacon['uuid'] in TILTS.keys():
                        # maintain same field names as pytilt in case someone wants to use that
                        process_tilt_data({
                            'color': TILTS[beacon['uuid']],
                            'timestamp': datetime.now().isoformat(),
                            'temp': beacon['major'], # fahrenheit
                            'gravity': beacon['minor']
                        })
        time.sleep(sleep_interval)

def distinct(objects):
    seen = set()
    unique = []
    for obj in objects:
        if obj['uuid'] not in seen:
            unique.append(obj)
            seen.add(obj['uuid'])
    return unique