import json, uuid
from pathlib import Path
from flask import *
from . import main
from .recipe_parser import PicoBrewRecipe
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


@main.route('/recipes')
def recipes():
    global recipes
    recipes = load_recipes()
    return render_template('recipes.html', recipes=recipes)


@main.route('/new_recipe')
def new_recipe():
    return render_template('new_recipe.html')


@main.route('/new_recipe_save', methods=['POST'])
def new_recipe_save():
    recipe = request.get_json()
    recipe['id'] = uuid.uuid4().hex[:14]
    filename = Path(RECIPE_PATH).joinpath('{}.json'.format(recipe['name'].replace(' ', '_')))
    if not filename.exists():
        with open(filename, "w") as file:
            json.dump(recipe, file, indent=4, sort_keys=True)
    return '', 204


def load_recipes():
    files = list(Path(RECIPE_PATH).glob("*.json"))
    recipes = [load_recipe(file) for file in files]
    return recipes


def load_recipe(file):
    recipe = PicoBrewRecipe()
    recipe.parse(file)
    return recipe


def get_recipes():
    global recipes
    return recipes


def load_active_brew_sessions():
    brew_sessions = []
    for uid in active_brew_sessions:
        brew_sessions.append({'alias': active_brew_sessions[uid].alias, 'graph': get_brew_graph_data(uid, active_brew_sessions[uid].name, active_brew_sessions[uid].step, active_brew_sessions[uid].data)})
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
    return({'date': info[0], 'name': name, 'graph': get_brew_graph_data(chart_id, name, step, json_data)})


def get_brew_graph_data(chart_id, session_name, session_step, session_data):
    wort_data = []
    block_data = []
    events = []
    for data in session_data:
        wort_data.append([data['time'], int(data['wort'])])
        block_data.append([data['time'], int(data['therm'])])
        if 'event' in data:
            events.append({'color': 'black', 'width': '2', 'value': data['time'], 'label': {'text': data['event'], 'style': {'color': 'white', 'fontWeight': 'bold'}, 'verticalAlign': 'top', 'x': -15, 'y': 0}})
    graph_data = {
        'chart_id': chart_id,
        'title': {'text': session_name},
        'subtitle': {'text': session_step},
        'series':  [{'name': 'Wort', 'data': wort_data}, {'name': 'Heat Block', 'data': block_data}],
        'xaplotlines': events
    }
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
recipes = load_recipes()
