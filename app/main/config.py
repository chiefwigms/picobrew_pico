from enum import Enum
from flask import current_app


class MachineType(str, Enum):
    def __str__(self):
        return str(self.value)

    PICOBREW_C = 'PicoBrewC'
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
    elif machineType is MachineType.PICOBREW_C:
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


# recipe paths
def recipe_path(machineType, archived=False):
    recipe_filepath = ""
    if machineType is MachineType.PICOBREW or machineType is MachineType.PICOBREW_C:
        recipe_filepath = current_app.config['RECIPES_PATH'].joinpath('pico')
    elif machineType is MachineType.ZYMATIC:
        recipe_filepath = current_app.config['RECIPES_PATH'].joinpath('zymatic')
    elif machineType is MachineType.ZSERIES:
        recipe_filepath = current_app.config['RECIPES_PATH'].joinpath('zseries')
    else:
        raise Exception("recipe_path: unsupported machine type {machineType}")

    if archived:
        recipe_filepath = recipe_filepath.joinpath('archive')

    return recipe_filepath


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
