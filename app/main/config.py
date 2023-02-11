from enum import Enum
from flask import current_app


class MachineType(str, Enum):
    def __str__(self):
        return str(self.value)

    PICOBREW_C = 'PicoBrewC'
    PICOBREW_C_ALT = 'PicoBrewC_Alt'
    PICOBREW = 'PicoBrew'
    PICOFERM = 'PicoFerm'
    PICOSTILL = 'PicoStill'
    ZSERIES = 'ZSeries'
    ZYMATIC = 'Zymatic'
    ISPINDEL = 'iSpindel'
    TILT = 'Tilt'


class SessionType(str, Enum):
    def __str__(self):
        return str(self.value)

    BREW = 'brew'
    PICOSTILL = 'still'
    PICOFERM = 'ferm'
    TILT = 'tilt'
    ISPINDEL = 'iSpindel'


# server config
def server_config():
    return current_app.config['SERVER_CONFIG']


# base path
def base_path():
    return current_app.config['BASE_PATH']


# firmware paths
def firmware_path(machineType):
    if machineType is MachineType.PICOBREW:
        return current_app.config['FIRMWARE_PATH'].joinpath('pico')
    elif machineType in [MachineType.PICOBREW_C, MachineType.PICOBREW_C_ALT]:
        return current_app.config['FIRMWARE_PATH'].joinpath('pico_c')
    elif machineType is MachineType.ZYMATIC:
        return current_app.config['FIRMWARE_PATH'].joinpath('zymatic')
    elif machineType is MachineType.ZSERIES:
        return current_app.config['FIRMWARE_PATH'].joinpath('zseries')
    elif machineType is MachineType.PICOSTILL:
        return current_app.config['FIRMWARE_PATH'].joinpath('picostill')
    elif machineType is MachineType.PICOFERM:
        return current_app.config['FIRMWARE_PATH'].joinpath('picoferm')
    else:
        raise Exception("firmware_path: unsupported machine type {machineType}")


# recipe path
def recipe_path(machineType, archived=False):
    filepath = current_app.config['RECIPES_PATH']
    if machineType in [MachineType.PICOBREW, MachineType.PICOBREW_C, MachineType.PICOBREW_C_ALT]:
        filepath = filepath.joinpath('pico')
    elif machineType is MachineType.ZYMATIC:
        filepath = filepath.joinpath('zymatic')
    elif machineType is MachineType.ZSERIES:
        filepath = filepath.joinpath('zseries')
    else:
        raise Exception("recipe_path: unsupported machine type {machineType}")

    if archived:
        filepath = filepath.joinpath('archive')

    return filepath


# session path
def session_path(sessionType, archived=False):
    try:
        filepath = current_app.config['SESSIONS_PATH'].joinpath(SessionType(sessionType))
    except:
        raise Exception("session_path: unsupported session type {sessionType}")

    if archived:
        filepath = filepath.joinpath('archive')
    else:
        filepath = filepath.joinpath('active')

    return filepath


# sessions paths
def brew_active_sessions_path():
    return current_app.config['SESSIONS_PATH'].joinpath('brew/active')


def brew_archive_sessions_path():
    return current_app.config['SESSIONS_PATH'].joinpath('brew/archive')


def ferm_active_sessions_path():
    return current_app.config['SESSIONS_PATH'].joinpath('ferm/active')


def ferm_archive_sessions_path():
    return current_app.config['SESSIONS_PATH'].joinpath('ferm/archive')


def still_active_sessions_path():
    return current_app.config['SESSIONS_PATH'].joinpath('still/active')


def still_archive_sessions_path():
    return current_app.config['SESSIONS_PATH'].joinpath('still/archive')


def iSpindel_active_sessions_path():
    return current_app.config['SESSIONS_PATH'].joinpath('iSpindel/active')


def iSpindel_archive_sessions_path():
    return current_app.config['SESSIONS_PATH'].joinpath('iSpindel/archive')


def tilt_active_sessions_path():
    return current_app.config['SESSIONS_PATH'].joinpath('tilt/active')


def tilt_archive_sessions_path():
    return current_app.config['SESSIONS_PATH'].joinpath('tilt/archive')
