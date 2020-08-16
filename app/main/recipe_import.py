import requests
from .recipe_parser import  PicoBrewRecipeImport,  ZymaticRecipeImport,ZSeriesRecipeImport
from .config import MachineType
from flask import current_app
SYNC_URI_TMPLS = {
    MachineType.PICOBREW: 'http://137.117.17.70/API/pico/getRecipe?uid={}&rfid={}&ibu=-1&abv=-1.0',
    MachineType.ZYMATIC: 'http://137.117.17.70/API/SyncUSer?user={}&machine={}'
}



class ImportException(Exception):
    pass

# id should be the rfid of a picopack, or a user GUID
def import_recipes(mach_uid: str, account_id: str, mach_type: MachineType):
    if mach_type == MachineType.ZYMATIC or mach_type == MachineType.PICOBREW:
        return import_recipes_classic(mach_uid, account_id, mach_type)
    elif mach_type == MachineType.ZSERIES:
        return import_recipes_z(mach_uid)


def import_recipes_classic(mach_uid, account_id, mach_type):
    try:
        uri = SYNC_URI_TMPLS[mach_type].format(mach_uid, account_id)
        repl = requests.get(uri, headers={'host': 'picobrew.com'})
        raw_reply = repl.text.strip()
    except Exception as e:
        raise ImportException(f'Error fetching via http: {e}')
    if raw_reply.startswith('#') and raw_reply.endswith('#') and raw_reply != '#Invalid|#':
        if mach_type is MachineType.PICOBREW:
            PicoBrewRecipeImport(raw_reply, account_id)
            return True
        elif mach_type is MachineType.ZYMATIC:
            current_app.logger.debug('Importing Zymatic recipe')
            ZymaticRecipeImport(raw_reply)
            return True
        else:
            raise ImportException('Invalid machine type')
    # Not reached
    return False

# Magic string in firmware
Z_AUTH_TOKEN='Bearer ZaLkGcvppNz7HYNeHhI3ViAS6hdmoUKgGTb6kTtNE90+taeO8VppoiH5qtm051xj6btIGcDEB6NVgJWkjDEoVw=='
def import_recipes_z(mach_uid: str):
    uri = f'https://137.117.17.70/Vendors/input.cshtml?ctl=RecipeRefListController&token={mach_uid}'
    session = requests.Session()
    session.headers = {'host': 'www.picobrew.com',
        'Authorization': Z_AUTH_TOKEN,
        'Content-Type': 'application/json'}
    repl = session.post(uri,verify=False,
        json={'Kind': 1, 'MaxCount': 20, 'Offset': 0},
        )
    if repl.status_code != 200:
        current_app.logger.debug(f'Failed to get recipe list: {repl.text}')
        return False
    recipe_list = repl.json()
    for recipe in recipe_list['Recipes']:
        id = recipe['ID']
        name = recipe['Name']
        current_app.logger.debug(f'DEBUG: fetching recipe {name}')
        session.headers = {'host': 'www.picobrew.com',
            'Authorization': Z_AUTH_TOKEN,
            }

        uri = f'https://137.117.17.70/Vendors/input.cshtml?type=Recipe&token={mach_uid}&id={id}'
        repl = session.get(uri, verify=False)
        if repl.status_code != 200:
            current_app.logger.debug("bad fetch")
            return False
        recipe = repl.json()
        ZSeriesRecipeImport(recipe)
    return True