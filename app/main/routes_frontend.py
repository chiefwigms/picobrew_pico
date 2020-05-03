import json, re, uuid
from pathlib import Path
from flask import *
from . import main
from .recipe_parser import PicoBrewRecipe
from .. import *
import sys

# -------- Routes --------
@main.route('/')
def index():
    return render_template('index.html', graph_data=get_graph_data('live_session', current_session.name, current_session.step, current_session.data))

@main.route('/history')
def history():
    return render_template('history.html', sessions=load_sessions())

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
    recipe['id'] =  uuid.uuid4().hex[:14]
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

def load_sessions():
    files = list(Path(SESSION_PATH).glob("*.json"))
    sessions = [load_session(file) for file in files]
    return sessions

def load_session(file):
    info = file.stem.split('#')
    #0 = Date, 1 = RFID, 2 = Session Name
    name = info[2].replace('_', ' ')
    step = ''
    with open(file) as fp:
        raw_data = fp.read().rstrip()
        if raw_data.endswith(','):
            #Recover from incomplete json data file
            raw_data = raw_data[:-1] + '\n]'
        json_data = json.loads(raw_data)
    chart_id = info[0]+info[1]
    return({'date':info[0], 'session':info[1], 'name':name, 'chart_id':chart_id, 'graph':get_graph_data(chart_id, name, step, json_data)})

def get_graph_data(chart_id, session_name, session_step, session_data):
    wort_data = []
    block_data = []
    events = []
    for data in session_data:
        wort_data.append([data['time'], int(data['wort'])])
        block_data.append([data['time'], int(data['therm'])])
        if 'event' in data:
            events.append({ 'color': 'black', 'width': '2', 'value': data['time'], 'label': {'text': data['event'], 'style': {'color': 'white', 'fontWeight': 'bold'}, 'verticalAlign': 'top', 'x': -15, 'y': 0}})
    graph_data = {
        'chart_id': chart_id,
        'title': {'text': session_name},
        'subtitle': {'text': session_step},
        'series':  [{'name': 'Wort', 'data': wort_data}, {'name': 'Heat Block', 'data': block_data}],
        'xaplotlines': events
    }
    return graph_data

#Read initial recipe list on load
recipes = load_recipes()
