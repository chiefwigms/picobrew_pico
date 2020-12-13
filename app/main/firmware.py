from .config import MachineType, server_config
from distutils.version import LooseVersion


def firmware_filename(device: MachineType, version: str):
    firmware_prefix = device.lower()
    if (device == MachineType.PICOBREW):
        firmware_prefix = "pico"
    if (device == MachineType.PICOBREW_C):
        firmware_prefix = "pico_c"
    return "{}_{}.bin".format(firmware_prefix, version.replace(".", "_"))


def firmware_upgrade_required(device: MachineType, version: str):
    return LooseVersion(version) < LooseVersion(minimum_firmware(device))


def minimum_firmware(device: MachineType):
    default_firmware = {
        MachineType.ZSERIES: '0.0.116',
        MachineType.PICOBREW_C: '0.1.34',
        MachineType.PICOBREW: '0.1.34',
        MachineType.PICOSTILL: '0.0.30',
        MachineType.PICOFERM: '0.2.6'
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
