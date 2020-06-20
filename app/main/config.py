from flask import current_app


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