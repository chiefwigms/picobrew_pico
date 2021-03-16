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


# server config
def server_config():
    return current_app.config['SERVER_CONFIG']


# base path
def base_path():
    return current_app.config['BASE_PATH']


# firmware paths
def zseries_firmware_path():
    return current_app.config['FIRMWARE_PATH'].joinpath('zseries')


def pico_firmware_path(machineType):
    if machineType is MachineType.PICOBREW:
        return current_app.config['FIRMWARE_PATH'].joinpath('pico')
    else:
        return current_app.config['FIRMWARE_PATH'].joinpath('pico_c')


def picostill_firmware_path():
    return current_app.config['FIRMWARE_PATH'].joinpath('picostill')


def picoferm_firmware_path():
    return current_app.config['FIRMWARE_PATH'].joinpath('picoferm')


# recipe paths
def zymatic_recipe_path():
    return current_app.config['RECIPES_PATH'].joinpath('zymatic')


def zseries_recipe_path():
    return current_app.config['RECIPES_PATH'].joinpath('zseries')


def pico_recipe_path():
    return current_app.config['RECIPES_PATH'].joinpath('pico')


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
