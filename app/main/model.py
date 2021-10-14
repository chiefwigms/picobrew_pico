from flask import current_app
import requests
import shutil
import json

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
        self.webhooks = []

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
        self.webhooks = []


class PicoStillSession:
    def __init__(self, uid=None):
        self.file = None
        self.filepath = None
        self.alias = ''
        self.ip_address = None
        self.device_id = uid
        self.uninit = True
        self.created_at = None
        self.name = 'Waiting To Distill'
        self.active = False
        self.session = ''   # session guid
        self.polling_thread = None
        self.data = []
        self.webhooks = []

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
        self.webhooks = []

    def start_still_polling(self):
        connect_failure = False
        failure_message = None
        still_data_uri = 'http://{}/data'.format(self.ip_address)
        try:
            current_app.logger.debug('DEBUG: Retrieve PicoStill Data - {}'.format(still_data_uri))
            r = requests.get(still_data_uri)
            datastring = r.text.strip()
        except Exception as e:
            current_app.logger.error(f'exception occured communicating to picostill {still_data_uri} : {e}')
            failure_message = f'unable to estaablish successful connection to {still_data_uri}'
            datastring = None
            connect_failure = True

        if not datastring or datastring[0] != '#':
            connect_failure = True
            failure_message = f'received unexpected response string from {still_data_uri}'
            current_app.logger.error(f'{failure_message} : {datastring}')

        if connect_failure:
            raise Exception(f'Failed to Start PicoStill Monitoring: {failure_message}')

        from .still_polling import new_still_session
        from .still_polling import FlaskThread

        thread = FlaskThread(target=new_still_session,
                             args=(self.ip_address, self.device_id),
                             daemon=True)
        thread.start()
        self.polling_thread = thread


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
        self.webhooks = []

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
        self.webhooks = []


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
        self.webhooks = []

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
        self.webhooks = []


class TiltSession:
    def __init__(self):
        self.file = None
        self.filepath = None
        self.alias = ''
        self.color = None
        self.active = False
        self.uninit = True
        self.rssi = None
        self.start_time = None
        self.data = []
        self.webhooks = []

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
        self.webhooks = []


class Webhook:
    def __init__(self, url=None, enabled=None, status="disabled"):
        self.url = url
        self.enabled = enabled
        self.status = status if not enabled and status == "disabled" else "enabled"

class SupportObject:
    def __init__(self):
        self.name = None
        self.logo = None
        self.manual = None
        self.faq = None
        self.instructional_videos = None
        self.misc_media = None

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)


class SupportMedia:
    def __init__(self, path, owner="Picobrew"):
        self.path = path
        self.owner = owner
