import requests
from .recipe_parser import (
    PicoBrewRecipeImport,
    ZymaticRecipeImport,
    ZSeriesRecipeImport,
)
from .config import MachineType
from flask import current_app
from typing import Optional


def PicoSyncURI(mach_uid: str, rfid: str) -> str:
    return f"http://137.117.17.70/API/pico/getRecipe?uid={mach_uid}&rfid={rfid}&ibu=-1&abv=-1.0"


def ZymaticSyncURI(mach_uid: str, account_id: str) -> str:
    return f"http://137.117.17.70/API/SyncUSer?user={account_id}&machine={mach_uid}"


def ZSeriesMetaSyncURI(mach_uid: str) -> str:
    return f"https://137.117.17.70/Vendors/input.cshtml?ctl=RecipeRefListController&token={mach_uid}"


def ZSeriesDataSyncURI(mach_uid: str, recipe_id: str) -> str:
    return f"https://137.117.17.70/Vendors/input.cshtml?type=Recipe&token={mach_uid}&id={recipe_id}"


class ImportException(Exception):
    pass


def import_recipes(mach_uid: str, account_id: str, rfid: str, mach_type: MachineType):
    if mach_type in [MachineType.ZYMATIC, MachineType.PICOBREW, MachineType.PICOBREW_C]:
        import_recipes_classic(mach_uid, account_id, rfid, mach_type)
    elif mach_type == MachineType.ZSERIES:
        import_recipes_z(mach_uid)


def import_recipes_classic(mach_uid, account_id, rfid, mach_type):
    try:
        if mach_type == MachineType.ZYMATIC:
            uri = ZymaticSyncURI(mach_uid, account_id)
        elif mach_type in [MachineType.PICOBREW, MachineType.PICOBREW_C]:
            uri = PicoSyncURI(mach_uid, rfid)
        else:
            raise Exception(f"Bad value for MachineType: {mach_type}")
        repl = requests.get(uri, headers={"host": "picobrew.com"})
        raw_reply = repl.text.strip()
    except Exception as e:
        raise ImportException(f"Error fetching via http: {e}")

    if (
        len(raw_reply) > 2
        and raw_reply.startswith("#")
        and raw_reply.endswith("#")
        and raw_reply != "#Invalid|#"
    ):
        if mach_type in [MachineType.PICOBREW, MachineType.PICOBREW_C]:
            PicoBrewRecipeImport(recipe=raw_reply, rfid=rfid)
        elif mach_type is MachineType.ZYMATIC:
            current_app.logger.debug(f"Importing Zymatic recipe {raw_reply}")
            ZymaticRecipeImport(recipes=raw_reply)
        else:
            raise ImportException("Invalid machine type")
    else:
        if mach_type is MachineType.ZYMATIC:
            raise ImportException("User GUID and/or Product ID are invalid or not associated")
        else:
            raise ImportException("Picopak RFID expired and/or Product ID is invalid")


# Magic string in firmware
Z_AUTH_TOKEN = "Bearer ZaLkGcvppNz7HYNeHhI3ViAS6hdmoUKgGTb6kTtNE90+taeO8VppoiH5qtm051xj6btIGcDEB6NVgJWkjDEoVw=="


def import_recipes_z(mach_uid: str):
    uri = ZSeriesMetaSyncURI(mach_uid)
    session = requests.Session()
    session.headers = requests.structures.CaseInsensitiveDict(
        {
            "host": "www.picobrew.com",
            "Authorization": Z_AUTH_TOKEN,
            "Content-Type": "application/json",
        }
    )

    repl = session.post(uri, verify=False, json={"Kind": 1, "MaxCount": 20, "Offset": 0})
    if repl.status_code != 200:
        failure_message = f"Failed to get recipe list: {repl.text}"
        raise ImportException(failure_message)
    recipe_list = repl.json()

    current_app.logger.debug(f"raw recipe response {recipe_list}")
    current_app.logger.debug(f"found {len(recipe_list['Recipes'])} recipes")

    for recipe in recipe_list["Recipes"]:
        rid = recipe["ID"]
        # recipes imported from brewcrafter have no ID and have external steps
        # Example of External Recipe Payload: {'ID': None, 'Name': 'Beekeeper Honey Brown', 'Kind': 2, 'Uri': 'https://www.brewcrafter.com/recipe/steps/4f202520-a28c-44a6-76d6-c1298652a4fb', 'Abv': -1, 'Ibu': -1} 
        if rid != None:
            name = recipe["Name"]
            current_app.logger.debug(f"fetching recipe id='{rid}' and name='{name}'")
            session.headers = requests.structures.CaseInsensitiveDict(
                {"host": "www.picobrew.com", "Authorization": Z_AUTH_TOKEN,}
            )

            uri = ZSeriesDataSyncURI(mach_uid, rid)
            repl = session.get(uri, verify=False)
            if repl.status_code != 200:
                raise ImportException(f"Error importing: {repl.text}")
            recipe = repl.json()

            current_app.logger.debug(f"import recipe {recipe}")
            ZSeriesRecipeImport(recipe)
