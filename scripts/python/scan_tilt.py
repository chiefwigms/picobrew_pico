import asyncio
import time
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


# rssi is is the 2's complement of the calibrated Tx Power
def get_rssi(data):
    #tx_power=struct.unpack('B', data)[0]
    tx_power = data[0]
    return -(256 - tx_power)


async def run():
    print("Scanning for tilts...")
    while True:
        devices = await BleakScanner.discover(10)
        for d in devices:
            # print(d)
            if d.metadata['manufacturer_data'] and 76 in d.metadata['manufacturer_data']:
                data = d.metadata['manufacturer_data'][76]
                # print(get_string(data))
                if bytearray(data[:2]) == bytearray(IBEACON_PROXIMITY_TYPE):
                    uuid = get_string(data[2:18])
                    if uuid in TILTS:
                        color = TILTS[uuid]
                        temp = get_number(data[18:20]) # farenheight
                        gravity = get_number(data[20:22]) # gravity * 1000; gravity * 10000 (pro)
                        tx_power = get_number(data[22:23])
                        rssi = get_rssi(data[22:23])

                        if gravity > 1000:
                            # tilt pro has 1 more digit of resolution for both temp and gravity readings
                            gravity = gravity / 10
                            temp = temp / 10
                            resolution = 'high'
                        else:
                            resolution = 'low'

                        print("uuid: {} color: {} temp: {} gravity: {} rssi: {} tx_power: {} resolution: {}".format(
                                    uuid,     color,   temp,      gravity,  rssi,      tx_power,     resolution))
        time.sleep(10)

loop = asyncio.get_event_loop()
loop.run_until_complete(run())
