import shutil
from .config import (MachineType, brew_archive_sessions_path, ferm_archive_sessions_path,
                     still_archive_sessions_path, iSpindel_archive_sessions_path, tilt_archive_sessions_path)

ZYMATIC_LOCATION = {
    'PassThru': '0',
    'Mash': '1',
    'Adjunct1': '2',
    'Adjunct2': '3',
    'Adjunct3': '4',
    'Adjunct4': '5',
    'Pause': '6',
}

ZSERIES_LOCATION = {
    'PassThru': '0',
    'Mash': '1',
    'Adjunct1': '2',
    'Adjunct2': '3',
    'Adjunct3': '4',
    'Adjunct4': '5',
    'Pause': '6',
}

PICO_LOCATION = {
    'Prime': '0',
    'Mash': '1',
    'PassThru': '2',
    'Adjunct1': '3',
    'Adjunct2': '4',
    'Adjunct3': '6',
    'Adjunct4': '5',
}

PICO_SESSION = {
    0: 'Brewing',
    1: 'Deep Clean',
    2: 'Sous Vide',
    4: 'Cold Brew',
    5: 'Manual Brew',
}


class PicoBrewSession:
    def __init__(self, machineType=None):
        self.file = None
        self.filepath = None
        self.alias = ''
        self.machine_type = machineType
        self.created_at = None
        self.name = 'Waiting To Brew'
        self.type = 0
        self.step = ''
        self.session = ''   # session guid
        self.id = -1        # session id (integer)
        self.recovery = ''
        self.remaining_time = None
        self.is_pico = True if machineType in [MachineType.PICOBREW, MachineType.PICOBREW_C] else False
        self.data = []

    def cleanup(self):
        if self.file and self.filepath:
            self.file.close()
            shutil.move(str(self.filepath), str(brew_archive_sessions_path()))
        self.file = None
        self.filepath = None
        self.created_at = None
        self.name = 'Waiting To Brew'
        self.type = 0
        self.step = ''
        self.session = ''
        self.id = -1
        self.recovery = ''
        self.remaining_time = None
        self.data = []


class PicoStillSession:
    def __init__(self):
        self.file = None
        self.filepath = None
        self.alias = ''
        self.ip_address = None
        self.uninit = True
        self.created_at = None
        self.name = 'Waiting To Distill'
        self.active = False
        self.session = ''   # session guid
        self.polling_thread = None
        self.data = []

    def cleanup(self):
        if self.file and self.filepath:
            self.file.close()
            shutil.move(str(self.filepath), str(still_archive_sessions_path()))
        self.file = None
        self.filepath = None
        self.uninit = True
        self.created_at = None
        self.name = 'Waiting To Distill'
        self.active = False
        self.polling_thread = None
        self.session = ''
        self.data = []


class PicoFermSession:
    def __init__(self):
        self.file = None
        self.filepath = None
        self.alias = ''
        self.active = False
        self.uninit = True
        self.voltage = '-'
        self.start_time = None
        self.data = []

    def cleanup(self):
        if self.file and self.filepath:
            self.file.close()
            shutil.move(str(self.filepath), str(ferm_archive_sessions_path()))
        self.file = None
        self.filepath = None
        self.uninit = True
        self.voltage = '-'
        self.start_time = None
        self.data = []


class iSpindelSession:
    def __init__(self):
        self.file = None
        self.filepath = None
        self.alias = ''
        self.active = False
        self.uninit = True
        self.voltage = '-'
        self.start_time = None
        self.data = []

    def cleanup(self):
        if self.file and self.filepath:
            self.file.close()
            shutil.move(str(self.filepath), str(
                iSpindel_archive_sessions_path()))
        self.file = None
        self.filepath = None
        self.uninit = True
        self.voltage = '-'
        self.start_time = None
        self.data = []


class TiltSession:
    def __init__(self):
        self.file = None
        self.filepath = None
        self.alias = ''
        self.active = False
        self.uninit = True
        self.rssi = None
        self.start_time = None
        self.data = []

    def cleanup(self):
        if self.file and self.filepath:
            self.file.close()
            shutil.move(str(self.filepath), str(
                tilt_archive_sessions_path()))
        self.file = None
        self.filepath = None
        self.uninit = True
        self.rssi = None
        self.start_time = None
        self.data = []


class SupportObject:
    def __init__(self):
        self.name = None
        self.manual_path = None
        self.faq_path = None
        self.instructional_videos_path = None
        self.misc_media = None
