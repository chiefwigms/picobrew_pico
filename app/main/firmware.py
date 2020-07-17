from .config import MachineType, server_config
from distutils.version import LooseVersion, StrictVersion

def firmware_filename(device: MachineType, version: str):
    if (device == MachineType.PICOBREW):
        return "pico_{}.bin".format(version.replace(".", "_"))
    return "{}_{}.bin".format(device.lower(), version.replace(".", "_"))


def firmware_upgrade_required(device: MachineType, version: str):
    return LooseVersion(version) < LooseVersion(minimum_firmware(device))


def minimum_firmware(device: MachineType):
    default_firmware = {
        MachineType.ZSERIES: '0.0.116',
        MachineType.PICOBREW: '0.1.34',
        MachineType.PICOSTILL: '0.0.30'
    }

    if device not in default_firmware:
        raise Exception('invalid device type {}'.format(device))

    if 'firmware' in server_config():
        firmware = server_config()['firmware'] or {}
        if firmware:
            return firmware.get(device, default_firmware[device])
        else:
            return default_firmware[device]
    else:
        return default_firmware[device]
