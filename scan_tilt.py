import asyncio
from bleak import BleakScanner

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
    'a495ff10c5b14b44b5121370f02d74de': 'Black',
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

async def run():
    print("Scanning for tilts...")
    devices = await BleakScanner.discover()
    for d in devices:
        # print(d)
        if d.metadata['manufacturer_data'] and 76 in d.metadata['manufacturer_data']:
            data = d.metadata['manufacturer_data'][76]
            #print(get_string(data))
            if bytearray(data[:2]) == bytearray(IBEACON_PROXIMITY_TYPE):
                uuid=get_string(data[2:18]).replace('-','')
                if uuid in TILTS:
                    #### begin test theory on real uuid (reliably being address)
                    real_uuid = d.metadata['uuids'][0] if ('uuids' in d.metadata and len(d.metadata['uuids']) > 0) else "unknown"
                    print("Found name: {} address: {} uuid: {} metadata: {}".format(d.name, d.address, real_uuid, d.metadata))
                    #### end test theory
                    color = TILTS[uuid]
                    temp=get_number(data[18:20]) # farenheight
                    gravity=get_number(data[20:22]) # gravity * 1000
                    rssi=get_number(data[-1:])
                    print("uuid: {} color: {} temp: {} gravity: {} rssi: {}".format(uuid, color, temp, gravity, rssi))


loop = asyncio.get_event_loop()
loop.run_until_complete(run())