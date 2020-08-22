import requests
from .recipe_parser import (
    PicoBrewRecipeImport,
    ZymaticRecipeImport,
    ZSeriesRecipeImport,
)
from .config import MachineType
from flask import current_app
from typing import Optional


def PicoSyncURI(mach_uid: str, account_id: str) -> str:
    return f"http://137.117.17.70/API/pico/getRecipe?uid={mach_uid}&rfid={account_id}&ibu=-1&abv=-1.0"


def ZymaticSyncURI(mach_uid: str, account_id: str) -> str:
    return f"http://137.117.17.70/API/SyncUSer?user={account_id}&machine={mach_uid}"


def ZSeriesMetaSyncURI(mach_uid: str) -> str:
    return f"https://137.117.17.70/Vendors/input.cshtml?ctl=RecipeRefListController&token={mach_uid}"


def ZSeriesDataSyncURI(mach_uid: str, recipe_id: str) -> str:
    return f"https://137.117.17.70/Vendors/input.cshtml?type=Recipe&token={mach_uid}&id={recipe_id}"


class ImportException(Exception):
    pass


# id should be the rfid of a picopack, or a user GUID
def import_recipes(mach_uid: str, account_id: Optional[str], mach_type: MachineType):
    if mach_type == MachineType.ZYMATIC or mach_type == MachineType.PICOBREW:
        return import_recipes_classic(mach_uid, account_id, mach_type)
    elif mach_type == MachineType.ZSERIES:
        return import_recipes_z(mach_uid)


def import_recipes_classic(mach_uid, account_id, mach_type):
    try:
        if mach_type == MachineType.ZYMATIC:
            uri = ZymaticSyncURI(mach_uid, account_id)
        elif mach_type == MachineType.PICOBREW:
            uri = PicoSyncURI(mach_uid, account_id)
        else:
            raise Exception(f"Bad value for MachineType: {mach_type}")
        repl = requests.get(uri, headers={"host": "picobrew.com"})
        raw_reply = repl.text.strip()
    except Exception as e:
        raise ImportException(f"Error fetching via http: {e}")
    print(raw_reply)
    if (
        len(raw_reply) > 2
        and raw_reply.startswith("#")
        and raw_reply.endswith("#")
        and raw_reply != "#Invalid|#"
    ):
        if mach_type is MachineType.PICOBREW:
            PicoBrewRecipeImport(recipe=raw_reply, rfid=account_id)
            return True
        elif mach_type is MachineType.ZYMATIC:
            current_app.logger.debug("Importing Zymatic recipe")
            ZymaticRecipeImport(recipes=raw_reply)
            return True
        else:
            raise ImportException("Invalid machine type")
    # Not reached
    return False


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
    repl = session.post(
        uri, verify=False, json={"Kind": 1, "MaxCount": 20, "Offset": 0},
    )
    if repl.status_code != 200:
        current_app.logger.debug(f"Failed to get recipe list: {repl.text}")
        return False
    recipe_list = repl.json()
    for recipe in recipe_list["Recipes"]:
        id = recipe["ID"]
        name = recipe["Name"]
        current_app.logger.debug(f"fetching recipe {name}")
        session.headers = requests.structures.CaseInsensitiveDict(
            {"host": "www.picobrew.com", "Authorization": Z_AUTH_TOKEN,}
        )

        uri = ZSeriesDataSyncURI(mach_uid, id)
        repl = session.get(uri, verify=False)
        if repl.status_code != 200:
            current_app.logger.debug("bad fetch")
            return False
        recipe = repl.json()
        ZSeriesRecipeImport(recipe)
    return True
