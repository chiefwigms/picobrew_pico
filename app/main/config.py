from enum import Enum
from flask import current_app


class MachineType(str, Enum):
    PICOBREW = 'PicoBrew'
    PICOFERM = 'PicoFerm'
    PICOSTILL = 'PicoStill'
    ZSERIES = 'ZSeries'
    ZYMATIC = 'Zymatic'


# server config
def server_config():
    return current_app.config['SERVER_CONFIG']


# base path
def base_path():
    return current_app.config['BASE_PATH']


# firmware paths
def zseries_firmware_path():
    return current_app.config['FIRMWARE_PATH'].joinpath('zseries')


def pico_firmware_path():
    return current_app.config['FIRMWARE_PATH'].joinpath('pico')


def picostill_firmware_path():
    return current_app.config['FIRMWARE_PATH'].joinpath('picostill')


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
