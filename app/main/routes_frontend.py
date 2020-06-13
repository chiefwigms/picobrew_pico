import json
import requests
import uuid
from flask import *
from pathlib import Path

from . import main
from .recipe_parser import PicoBrewRecipe, PicoBrewRecipeImport, ZymaticRecipe, ZymaticRecipeImport, ZSeriesRecipe
from .. import *


# -------- Routes --------
@main.route('/')
def index():
    return render_template('index.html', brew_sessions=load_active_brew_sessions(),
                           ferm_sessions=load_active_ferm_sessions())


@main.route('/brew_history')
def brew_history():
    return render_template('brew_history.html', sessions=load_brew_sessions())


@main.route('/ferm_history')
def ferm_history():
    return render_template('ferm_history.html', sessions=load_ferm_sessions())


@main.route('/zymatic_recipes')
def _zymatic_recipes():
    global zymatic_recipes
    zymatic_recipes = load_zymatic_recipes()
    return render_template('zymatic_recipes.html', recipes=zymatic_recipes)


@main.route('/new_zymatic_recipe', methods=['GET', 'POST'])
def new_zymatic_recipe():
    if request.method == 'POST':
        recipe = request.get_json()
        recipe['id'] = uuid.uuid4().hex[:32]
        filename = Path(ZYMATIC_RECIPE_PATH).joinpath('{}.json'.format(recipe['name'].replace(' ', '_')))
        if not filename.exists():
            with open(filename, "w") as file:
                json.dump(recipe, file, indent=4, sort_keys=True)
            return '', 204
        else:
            return 'Recipe Exists!', 418
    else:
        return render_template('new_zymatic_recipe.html')


@main.route('/import_zymatic_recipe', methods=['GET', 'POST'])
def import_zymatic_recipe():
    if request.method == 'POST':
        recipes = ''
        data = request.get_json()
        guid = data['guid']
        machine = next((uid for uid in active_brew_sessions if not active_brew_sessions[uid].is_pico), None)
        try:
            r = requests.get('http://picobrew.com/API/SyncUSer?user={}&machine={}'.format(guid, machine))
            recipes = r.text.strip()
        except:
            pass
        print('DEBUG: Zymatic Recipes Dumped: \"{}\"'.format(recipes))
        if len(recipes) > 2 and recipes[0] == '#' and recipes[-1] == '#':
            ZymaticRecipeImport(recipes)
            return '', 204
        else:
            return 'Import Failed: \"' + recipes + '\"', 418
    else:
        return render_template('import_zymatic_recipe.html')


def load_zymatic_recipes():
    files = list(Path(ZYMATIC_RECIPE_PATH).glob("*.json"))
    recipes = [load_zymatic_recipe(file) for file in files]
    return recipes


def load_zymatic_recipe(file):
    recipe = ZymaticRecipe()
    recipe.parse(file)
    return recipe


def get_zymatic_recipes():
    global zymatic_recipes
    return zymatic_recipes


@main.route('/zseries_recipes')
def zseries_recipes():
    global zseries_recipes
    zseries_recipes = load_zseries_recipes()
    return render_template('zseries_recipes.html', recipes=zseries_recipes)


@main.route('/new_zseries_recipe')
def new_zseries_recipe():
    return render_template('new_zseries_recipe.html')


@main.route('/new_zseries_recipe_save', methods=['POST'])
def new_zseries_recipe_save():
    recipe = request.get_json()
    recipe['id'] = increment_zseries_recipe_id()
    recipe['start_water'] = 13.1
    filename = Path(ZSERIES_RECIPE_PATH).joinpath('{}.json'.format(recipe['name'].replace(' ', '_')))
    if not filename.exists():
        with open(filename, "w") as file:
            json.dump(recipe, file, indent=4, sort_keys=True)
        return '', 204
    else:
        return 'Recipe Exists!', 418


def load_zseries_recipes():
    files = list(Path(ZSERIES_RECIPE_PATH).glob("*.json"))
    recipes = [load_zseries_recipe(file) for file in files]
    return recipes


def load_zseries_recipe(file):
    recipe = ZSeriesRecipe()
    recipe.parse(file)
    return recipe


def get_zseries_recipes():
    global zseries_recipes
    return zseries_recipes


@main.route('/pico_recipes')
def _pico_recipes():
    global pico_recipes
    pico_recipes = load_pico_recipes()
    return render_template('pico_recipes.html', recipes=pico_recipes)


@main.route('/new_pico_recipe', methods=['GET', 'POST'])
def new_pico_recipe():
    if request.method == 'POST':
        recipe = request.get_json()
        recipe['id'] = uuid.uuid4().hex[:14]
        recipe[
            'image'] = '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffe000ffc01ffffc0000000000000003fff0003f601ff7ff0000000000000000fe7c00dff003de7f8000800030000000ff3e000ff801ff7f80078001fe000000dfbe000ff801feff80070001fe0000009c37000de000dffc0007803ffe0000021c070001c000cbf80007803ffe000000dcbf800dc0002ff0000780ffff000000fc9f800fc0003fe00007a3ffff800003fc1f800fc0000dc00007ffffff000003fc3f801dc0000fc00007f1f8bf000002bcb7800dc0000dc00007f0f9fffc00003c278001c00021c00007f079ff0600023c0f8021c00021c00007fe10fe0200003c1f8001c00021c00007e000ff00000c1c3f00c1c000c1c00007e080ff00000000fe0080600000600007e010ff00000ffffc00fff000fff00007e001ff00000ffff800fff800fff80007e001ff000007ffe0007ff8003ff80007f000fe00000000000000000000000007f001fe00fffe03fff003fffcfffbff87f001fe001fffc0ffff03fffcffffffc7e0007e00cfff633c3f807e3e1cfdede7e0017e006fffb13f9fc03f9f3dfdefe7e0017e000ffff8bfefc03fdf3cffe7e7e0017e0007eef8b7ffe037df1cfdf787f0017e0001e6bc87a7e0073f18f8ff07f0017e0005cc3c841bf02fbf1aefff07f8dffe02070d7c3c3ff030df1e4ece07fdffff8c24067c303fe0ffe00e0e4e07fdffff003df778f79bc0ffe00f1f0e07fddffe010dff30bfcdf0afec0f1f0e07fc08ff7015fd38afedb82fce0f1e1e07fffffe0001e4388f21bc8f0f061e1c07fffffc0001e03c8f203c0f4f061e1c07e0017c0061f07f07003d078f063e1c07c0003e000000fe01987c000f033f1c03e0007c00ffffffffcfffffff03fff800ff9ff000fffffbffeffbffff03fbf800000000007fffe1ffe3f1ffff00f9f800000000001fff00ffc0c0fffe007070000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
        filename = Path(PICO_RECIPE_PATH).joinpath('{}.json'.format(recipe['name'].replace(' ', '_')))
        if not filename.exists():
            with open(filename, "w") as file:
                json.dump(recipe, file, indent=4, sort_keys=True)
            return '', 204
        else:
            return 'Recipe Exists!', 418
    else:
        return render_template('new_pico_recipe.html')


@main.route('/import_pico_recipe', methods=['GET', 'POST'])
def import_pico_recipe():
    if request.method == 'POST':
        recipe = ''
        data = request.get_json()
        rfid = data['rfid']
        uid = next((uid for uid in active_brew_sessions if active_brew_sessions[uid].is_pico), None)
        try:
            r = requests.get('http://picobrew.com/API/pico/getRecipe?uid={}&rfid={}&ibu=-1&abv=-1.0'.format(uid, rfid))
            recipe = r.text.strip()
        except:
            pass
        print('DEBUG: Pico Recipe Dumped: \"{}\"'.format(recipe))
        if len(recipe) > 2 and recipe[0] == '#' and recipe[-1] == '#' and recipe != '#Invalid|#':
            PicoBrewRecipeImport(recipe, rfid)
            return '', 204
        else:
            return 'Import Failed: \"' + recipe + '\"', 418
    else:
        return render_template('import_pico_recipe.html')


def load_pico_recipes():
    files = list(Path(PICO_RECIPE_PATH).glob("*.json"))
    recipes = [load_pico_recipe(file) for file in files]
    return recipes


def load_pico_recipe(file):
    recipe = PicoBrewRecipe()
    recipe.parse(file)
    return recipe


def get_pico_recipes():
    global pico_recipes
    return pico_recipes


def load_active_brew_sessions():
    brew_sessions = []
    for uid in active_brew_sessions:
        brew_sessions.append({'alias': active_brew_sessions[uid].alias,
                              'graph': get_brew_graph_data(uid, active_brew_sessions[uid].name,
                                                           active_brew_sessions[uid].step,
                                                           active_brew_sessions[uid].data,
                                                           active_brew_sessions[uid].is_pico)})
    return brew_sessions


def load_brew_sessions():
    files = list(Path(BREW_ARCHIVE_PATH).glob("*.json"))
    brew_sessions = [load_brew_session(file) for file in files]
    return brew_sessions


def load_brew_sessions_by_machine(uid):
    files = list(Path(BREW_ARCHIVE_PATH).glob("*#{}*.json".format(uid)))
    brew_sessions = [load_brew_session(file) for file in files]
    return brew_sessions


def load_brew_session(file):
    info = file.stem.split('#')

    # 0 = Date, 1 = UID, 2 = RFID / Session GUID (guid), 3 = Session Name, 4 = Session Type (integer - z only)
    name = info[3].replace('_', ' ')

    step = ''
    with open(file) as fp:
        raw_data = fp.read().rstrip()
        if raw_data.endswith(','):
            # Recover from incomplete json data file
            raw_data = raw_data[:-1] + '\n]'
        json_data = json.loads(raw_data)
    chart_id = info[0] + '_' + info[2]

    alias = '' if info[1] not in active_brew_sessions else active_brew_sessions[info[1]].alias

    session_type = None
    if len(info) >= 4:
        session_type = int(info[4])

    session = {
        'date': info[0],
        'name': name,
        'uid': info[1],
        'type': session_type,
        'alias': alias,
        'graph': get_brew_graph_data(chart_id, name, step, json_data)
    }
    return (session)


def get_brew_graph_data(chart_id, session_name, session_step, session_data, is_pico=None):
    wort_data = []  # Shared

    block_data = []  # Pico and ZSeries Only

    board_data = []  # Zymatic Only
    heat1_data = []  # Zymatic Only
    heat2_data = []  # Zymatic Only

    target_data = []  # ZSeries Only
    drain_data = []  # ZSeries Only
    ambient_data = []  # ZSeries Only
    valve_position = []  # ZSeries Only

    events = []
    for data in session_data:
        if all(k in data for k in ('therm', 'wort')):  # Pico and ZSeries
            wort_data.append([data['time'], int(data['wort'])])
            block_data.append([data['time'], int(data['therm'])])

        if all(k in data for k in ('target', 'drain', 'ambient', 'position')):  # ZSeries
            target_data.append([data['time'], int(data['target'])])
            drain_data.append([data['time'], int(data['drain'])])
            ambient_data.append([data['time'], int(data['ambient'])])
            # TODO figure out how to add `position`, `pause_state` and `error` to the graphs?
            valve_position.append([data['time'], int(data['position'])])

        if all(k in data for k in ('wort', 'board', 'heat1', 'heat2')):  # Zymatic
            wort_data.append([data['time'], int(data['wort'])])
            board_data.append([data['time'], int(data['board'])])
            heat1_data.append([data['time'], int(data['heat1'])])
            heat2_data.append([data['time'], int(data['heat2'])])

        # add an overlay event for each step
        if 'event' in data:
            events.append({'color': 'black', 'width': '2', 'value': data['time'],
                           'label': {'text': data['event'], 'style': {'color': 'white', 'fontWeight': 'bold'},
                                     'verticalAlign': 'top', 'x': -15, 'y': 0}})

    graph_data = {
        'chart_id': chart_id,
        'title': {'text': session_name},
        'subtitle': {'text': session_step},
        'xaplotlines': events
    }
    if len(ambient_data) > 0:
        graph_data.update({'series': [
            {'name': 'Target', 'data': target_data},
            {'name': 'Wort', 'data': wort_data},
            {'name': 'Heat Exchanger', 'data': block_data},
            {'name': 'Drain', 'data': drain_data},
            {'name': 'Ambient', 'data': ambient_data}
        ]})
    elif len(block_data) > 0 or is_pico:
        graph_data.update({'series': [
            {'name': 'Wort', 'data': wort_data},
            {'name': 'Heat Block', 'data': block_data}
        ]})
    else:
        graph_data.update({'series': [
            {'name': 'Heat Loop', 'data': heat1_data},
            {'name': 'Wort', 'data': wort_data},
            {'name': 'Board', 'data': board_data},
            {'name': 'Heat Loop 2', 'data': heat2_data}
        ]})
    return graph_data


def load_active_ferm_sessions():
    ferm_sessions = []
    for uid in active_ferm_sessions:
        ferm_sessions.append({'alias': active_ferm_sessions[uid].alias,
                              'graph': get_ferm_graph_data(uid, active_ferm_sessions[uid].voltage,
                                                           active_ferm_sessions[uid].data)})
    return ferm_sessions


def load_ferm_sessions():
    files = list(Path(FERM_ARCHIVE_PATH).glob("*.json"))
    ferm_sessions = [load_ferm_session(file) for file in files]
    return ferm_sessions


def load_ferm_session(file):
    info = file.stem.split('#')
    # 0 = Date, 1 = Device UID
    with open(file) as fp:
        raw_data = fp.read().rstrip()
        if raw_data.endswith(','):
            # Recover from incomplete json data file
            raw_data = raw_data[:-1] + '\n]'
        json_data = json.loads(raw_data)
    chart_id = info[0] + '_' + info[1]
    name = info[1]
    if info[1] in active_ferm_sessions:
        name = active_ferm_sessions[info[1]].alias
    return ({
        'date': info[0],
        'name': name,
        'graph': get_ferm_graph_data(chart_id, None, json_data)
    })


def get_ferm_graph_data(chart_id, voltage, session_data):
    temp_data = []
    pres_data = []
    for data in session_data:
        temp_data.append([data['time'], float(data['temp'])])
        pres_data.append([data['time'], float(data['pres'])])
    graph_data = {
        'chart_id': chart_id,
        'title': {'text': 'Fermentation'},
        'series': [
            {
                'name': 'Temperature',
                'data': temp_data
            }, {
                'name': 'Pressure',
                'data': pres_data,
                'yAxis': 1
            }
        ],
    }
    if voltage:
        graph_data.update({'subtitle': {'text': 'Voltage: ' + voltage}})
    return graph_data


# Read initial recipe list on load
pico_recipes = load_pico_recipes()
zymatic_recipes = load_zymatic_recipes()
zseries_recipes = load_zseries_recipes()


# utilities

def increment_zseries_recipe_id():
    recipe_id = -1
    for r in get_zseries_recipes():
        if r.id > recipe_id:
            recipe_id = r.id

    return recipe_id + 1
