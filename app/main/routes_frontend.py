import json, uuid
from pathlib import Path
from flask import *
from . import main
from .recipe_parser import PicoBrewRecipe, ZymaticRecipe
from .. import *
import sys


# -------- Routes --------
@main.route('/')
def index():
    return render_template('index.html', brew_sessions=load_active_brew_sessions(), ferm_sessions=load_active_ferm_sessions())


@main.route('/brew_history')
def brew_history():
    return render_template('brew_history.html', sessions=load_brew_sessions())


@main.route('/ferm_history')
def ferm_history():
    return render_template('ferm_history.html', sessions=load_ferm_sessions())


@main.route('/zymatic_recipes')
def zymatic_recipes():
    global zymatic_recipes
    zymatic_recipes = load_zymatic_recipes()
    return render_template('zymatic_recipes.html', recipes=zymatic_recipes)


@main.route('/new_zymatic_recipe')
def new_zymatic_recipe():
    return render_template('new_zymatic_recipe.html')


@main.route('/new_zymatic_recipe_save', methods=['POST'])
def new_zymatic_recipe_save():
    recipe = request.get_json()
    recipe['id'] = uuid.uuid4().hex[:32]
    filename = Path(ZYMATIC_RECIPE_PATH).joinpath('{}.json'.format(recipe['name'].replace(' ', '_')))
    if not filename.exists():
        with open(filename, "w") as file:
            json.dump(recipe, file, indent=4, sort_keys=True)
    return '', 204


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


@main.route('/pico_recipes')
def pico_recipes():
    global pico_recipes
    pico_recipes = load_pico_recipes()
    return render_template('pico_recipes.html', recipes=pico_recipes)


@main.route('/new_pico_recipe')
def new_pico_recipe():
    return render_template('new_pico_recipe.html')


@main.route('/new_pico_recipe_save', methods=['POST'])
def new_pico_recipe_save():
    recipe = request.get_json()
    recipe['id'] = uuid.uuid4().hex[:14]
    filename = Path(PICO_RECIPE_PATH).joinpath('{}.json'.format(recipe['name'].replace(' ', '_')))
    if not filename.exists():
        with open(filename, "w") as file:
            json.dump(recipe, file, indent=4, sort_keys=True)
    return '', 204


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
        brew_sessions.append({'alias': active_brew_sessions[uid].alias, 'graph': get_brew_graph_data(uid, active_brew_sessions[uid].name, active_brew_sessions[uid].step, active_brew_sessions[uid].data, active_brew_sessions[uid].is_pico)})
    return brew_sessions


def load_brew_sessions():
    files = list(Path(BREW_ARCHIVE_PATH).glob("*.json"))
    brew_sessions = [load_brew_session(file) for file in files]
    return brew_sessions


def load_brew_session(file):
    info = file.stem.split('#')
    # 0 = Date, 1 = UID, 2 = RFID, 3 = Session Name
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
    return({'date': info[0], 'name': name, 'alias': alias, 'graph': get_brew_graph_data(chart_id, name, step, json_data)})


def get_brew_graph_data(chart_id, session_name, session_step, session_data, is_pico=None):
    wort_data = []  # Shared
    block_data = []  # Pico Only
    board_data = []  # Zymatic Only
    heat1_data = []  # Zymatic Only
    heat2_data = []  # Zymatic Only
    events = []
    for data in session_data:
        if 'therm' in data:
            wort_data.append([data['time'], int(data['wort'])])
            block_data.append([data['time'], int(data['therm'])])
        else:
            wort_data.append([data['time'], int(data['wort'])])
            board_data.append([data['time'], int(data['board'])])
            heat1_data.append([data['time'], int(data['heat1'])])
            heat2_data.append([data['time'], int(data['heat2'])])
        if 'event' in data:
            events.append({'color': 'black', 'width': '2', 'value': data['time'], 'label': {'text': data['event'], 'style': {'color': 'white', 'fontWeight': 'bold'}, 'verticalAlign': 'top', 'x': -15, 'y': 0}})
    graph_data = {
        'chart_id': chart_id,
        'title': {'text': session_name},
        'subtitle': {'text': session_step},
        'xaplotlines': events
    }
    if len(block_data) > 0 or is_pico:
        graph_data.update({'series':  [{'name': 'Wort', 'data': wort_data}, {'name': 'Heat Block', 'data': block_data}]})
    else:
        graph_data.update({'series':  [{'name': 'Wort', 'data': wort_data}, {'name': 'Heat Loop', 'data': heat1_data}, {'name': 'Heat Loop 2', 'data': heat2_data}, {'name': 'Board', 'data': board_data}]})
    return graph_data


def load_active_ferm_sessions():
    ferm_sessions = []
    for uid in active_ferm_sessions:
        ferm_sessions.append({'alias': active_ferm_sessions[uid].alias, 'graph': get_ferm_graph_data(uid, active_ferm_sessions[uid].voltage, active_ferm_sessions[uid].data)})
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
    return({'date': info[0], 'name': name, 'graph': get_ferm_graph_data(chart_id, None, json_data)})


def get_ferm_graph_data(chart_id, voltage, session_data):
    temp_data = []
    pres_data = []
    for data in session_data:
        temp_data.append([data['time'], float(data['temp'])])
        pres_data.append([data['time'], float(data['pres'])])
    graph_data = {
        'chart_id': chart_id,
        'title': {'text': 'Fermentation'},
        'series':  [{'name': 'Temperature', 'data': temp_data}, {'name': 'Pressure', 'data': pres_data, 'yAxis': 1}],
    }
    if voltage:
        graph_data.update({'subtitle': {'text': 'Voltage: ' + voltage}})
    return graph_data


# Read initial recipe list on load
pico_recipes = load_pico_recipes()
zymatic_recipes = load_zymatic_recipes()
