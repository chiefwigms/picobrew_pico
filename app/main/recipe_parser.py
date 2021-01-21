import json
import uuid

from .config import zymatic_recipe_path, pico_recipe_path, zseries_recipe_path
from .model import PICO_LOCATION, ZYMATIC_LOCATION, ZSERIES_LOCATION
from flask import current_app


class ZymaticRecipeStep():
    def __init__(self):
        self.name = None
        self.temperature = None
        self.step_time = None
        self.location = None
        self.drain_time = None

    def serialize(self):
        return '{0},{1},{2},{3},{4}/'.format(
            self.name,
            self.temperature,
            self.step_time,
            ZYMATIC_LOCATION[self.location],
            self.drain_time
        )


class ZymaticRecipe():
    def __init__(self):
        self.clean = False
        self.id = None
        self.name = None
        self.name_ = None
        self.notes = None
        self.steps = []

    def parse(self, file):
        recipe = None
        with open(file) as f:
            recipe = json.load(f)
        self.clean = recipe.get('clean', False) or False
        self.id = recipe.get('id', 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX') or 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        self.name = recipe.get('name', 'Empty Recipe') or 'Empty Recipe'
        self.name_ = self.name.replace(" ", "_").replace("\'", "")
        self.notes = recipe.get('notes', None) or None
        if 'steps' in recipe:
            for recipe_step in recipe['steps']:
                step = ZymaticRecipeStep()
                step.name = recipe_step.get('name', 'Empty Step') or 'Empty Step'
                step.temperature = 70 if 'temperature' not in recipe_step else int(recipe_step['temperature'])
                step.step_time = 0 if 'step_time' not in recipe_step else int(recipe_step['step_time'])
                step.location = recipe_step.get('location', 'PassThru') or 'PassThru'
                step.drain_time = 0 if 'drain_time' not in recipe_step else int(recipe_step['drain_time'])
                self.steps.append(step)

    def serialize(self):
        steps = map(lambda step: step.serialize(), self.steps)
        return '{0}/{1}/{2}|'.format(
            self.name,
            self.id,
            ''.join(steps)
        )

    def update_steps(self, file, steps):
        self.steps = []
        for s in steps:
            step = ZymaticRecipeStep()
            step.name = s.get('name', 'Empty Step') or 'Empty Step'
            step.temperature = 70 if 'temperature' not in s else int(s['temperature'])
            step.step_time = 0 if 'step_time' not in s else int(s['step_time'])
            step.location = s.get('location', 'PassThru') or 'PassThru'
            step.drain_time = 0 if 'drain_time' not in s else int(s['drain_time'])
            self.steps.append(step)
        updated_recipe = json.loads(json.dumps(self, default=lambda r: r.__dict__))
        del updated_recipe['name_']
        with open(file, 'w') as f:
            json.dump(updated_recipe, f, indent=4, sort_keys=True)


def ZymaticRecipeImport(recipes):
    for recipe in recipes.strip('#|').split('|'):
        r = {}
        steps = list(filter(None, recipe.split('/')))
        r['name'] = steps.pop(0)
        r['clean'] = False
        r['id'] = steps.pop(0)
        r['steps'] = []
        for step in steps:
            values = step.split(',')
            s = {}
            s['name'] = values[0]
            s['temperature'] = int(values[1])
            s['step_time'] = int(values[2])
            s['location'] = next(k for k, v in ZYMATIC_LOCATION.items() if v == values[3])
            s['drain_time'] = int(values[4])
            r['steps'].append(s)
        filename = zymatic_recipe_path().joinpath('{}.json'.format(r['name'].replace(' ', '_')))
        if not filename.exists():
            with open(filename, "w") as file:
                json.dump(r, file, indent=4, sort_keys=True)


class ZSeriesRecipeStep():
    def __init__(self):
        self.name = None
        self.temperature = None
        self.step_time = None
        self.location = None
        self.drain_time = None

    def serialize(self):
        step = {}
        step['Name'] = self.name
        step['Location'] = int(ZSERIES_LOCATION[self.location])
        step['Temp'] = int(self.temperature)
        step['Time'] = int(self.step_time)
        step['Drain'] = int(self.drain_time)
        return step


class ZSeriesRecipe():
    def __init__(self):
        self.id = None
        self.name = None
        self.name_ = None
        self.notes = None
        self.start_water = 13.1
        self.kind_code = 0
        self.type_code = None
        self.steps = []

    def parse(self, file):
        recipe = None
        with open(file) as f:
            recipe = json.load(f)
        # TODO should this just fail or increment the number to be unique?
        self.id = recipe.get('id', 0) or 0
        self.name = recipe.get('name', 'Empty Recipe') or 'Empty Recipe'
        self.name_ = self.name.replace(" ", "_").replace("\'", "")
        self.notes = recipe.get('notes', None) or None
        self.start_water = recipe.get('start_water', 13.1) or 13.1
        self.type_code = recipe.get('type_code', "Beer") or "Beer"
        if 'steps' in recipe:
            for recipe_step in recipe['steps']:
                step = ZSeriesRecipeStep()
                step.name = recipe_step.get('name', 'Empty Step') or 'Empty Step'
                step.temperature = 70 if 'temperature' not in recipe_step else int(recipe_step['temperature'])
                step.step_time = 0 if 'step_time' not in recipe_step else int(recipe_step['step_time'])
                step.location = recipe_step.get('location', 'PassThru') or 'PassThru'
                if step.location == 'PassThrough':
                    step.location = 'PassThru'
                step.drain_time = 0 if 'drain_time' not in recipe_step else int(recipe_step['drain_time'])
                self.steps.append(step)

    def serialize(self):
        r = {}
        r['ID'] = self.id
        r['Name'] = self.name
        r['StartWater'] = self.start_water
        r['Steps'] = []
        for step in self.steps:
            r['Steps'].append(step.serialize())
        return r

    def update_steps(self, file, steps):
        self.steps = []
        for s in steps:
            step = ZSeriesRecipeStep()
            step.name = s.get('name', 'Empty Step') or 'Empty Step'
            step.temperature = 70 if 'temperature' not in s else int(s['temperature'])
            step.step_time = 0 if 'step_time' not in s else int(s['step_time'])
            step.location = s.get('location', 'PassThru') or 'PassThru'
            if step.location == 'PassThrough':
                step.location = 'PassThru'
            step.drain_time = 0 if 'drain_time' not in s else int(s['drain_time'])
            self.steps.append(step)
        updated_recipe = json.loads(json.dumps(self, default=lambda r: r.__dict__))
        del updated_recipe['name_']
        del updated_recipe['kind_code']
        del updated_recipe['type_code']
        with open(file, 'w') as f:
            json.dump(updated_recipe, f, indent=4, sort_keys=True)


def ZSeriesRecipeImport(recipe):
    r = {}
    r['name'] = recipe['Name']
    name = recipe['Name']

    current_app.logger.debug(f'saving recipe {name}')

    r['clean'] = False
    # verify id is unique
    r['id'] = recipe['ID']
    r['start_water'] = recipe['StartWater']
    r['steps'] = []

    for step in recipe['Steps']:
        s = {}
        s['name'] = step['Name']
        s['temperature'] = step['Temp']
        s['step_time'] = step['Time']
        s['location'] = next(k for k, v in ZSERIES_LOCATION.items() if int(v) == step['Location'])
        s['drain_time'] = step['Drain']
        r['steps'].append(s)

    # This will cause a circular import
    # Perhaps re-factor "live state" out into its own module?
    # existing = load_zseries_recipes()
    # conflict = [old.id for old in existing if old.id == r['id']]
    # if conflict:
    #    current_app.logger.error(f'Conflicting Z-series recipe IDs: {conflicts}')
    #    return None

    recipe_name = r['name'].replace(' ', '_')
    filename = zseries_recipe_path().joinpath(f'{recipe_name}.json')
    if not filename.exists():
        with open(filename, "w") as file:
            json.dump(r, file, indent=4, sort_keys=True)


class PicoBrewRecipeStep():
    def __init__(self):
        self.name = None
        self.location = None
        self.temperature = None
        self.step_time = None
        self.drain_time = None

    def serialize(self):
        return '{0},{1},{2},{3},{4},'.format(
            self.temperature,
            self.step_time,
            self.drain_time,
            PICO_LOCATION[self.location],
            self.name
        )


class PicoBrewRecipe():
    def __init__(self):
        self.id = None
        self.name = None
        self.notes = None
        self.name_ = None
        self.abv_tweak = None
        self.ibu_tweak = None
        self.abv = None
        self.ibu = None
        self.image = None
        self.steps = []

    def parse(self, file):
        recipe = None
        with open(file) as f:
            recipe = json.load(f)
        self.id = recipe.get('id', 'XXXXXXXXXXXXXX') or 'XXXXXXXXXXXXXX'
        self.name = recipe.get('name', 'Empty Recipe') or 'Empty Recipe'
        self.name_ = self.name.replace(" ", "_").replace("\'", "")
        self.notes = recipe.get('notes', None) or None
        self.abv_tweak = recipe.get('abv_tweak', -1) or -1
        self.ibu_tweak = recipe.get('ibu_tweak', -1) or -1
        self.abv = recipe.get('abv', 6) or 6
        self.ibu = recipe.get('ibu', 40) or 40
        self.image = recipe.get('image', '') or ''
        if 'steps' in recipe:
            for recipe_step in recipe['steps']:
                step = PicoBrewRecipeStep()
                step.name = recipe_step.get('name', 'Empty Step') or 'Empty Step'
                step.location = recipe_step.get('location', 'PassThru') or 'PassThru'
                step.temperature = 70 if 'temperature' not in recipe_step else int(recipe_step['temperature'])
                step.step_time = 0 if 'step_time' not in recipe_step else int(recipe_step['step_time'])
                step.drain_time = 0 if 'drain_time' not in recipe_step else int(recipe_step['drain_time'])
                self.steps.append(step)

    def serialize(self):
        steps = map(lambda step: step.serialize(), self.steps)
        return '{0}/{1},{2},{3},{4},{5}|{6}|'.format(
            self.name,
            self.abv_tweak,
            self.ibu_tweak,
            self.abv,
            self.ibu,
            ''.join(steps),
            self.image
        )

    def update_steps(self, file, steps):
        self.steps = []
        for s in steps:
            step = PicoBrewRecipeStep()
            step.name = s.get('name', 'Empty Step') or 'Empty Step'
            step.location = s.get('location', 'PassThru') or 'PassThru'
            step.temperature = 70 if 'temperature' not in s else int(s['temperature'])
            step.step_time = 0 if 'step_time' not in s else int(s['step_time'])
            step.drain_time = 0 if 'drain_time' not in s else int(s['drain_time'])
            self.steps.append(step)
        updated_recipe = json.loads(json.dumps(self, default=lambda r: r.__dict__))
        del updated_recipe['name_']
        with open(file, 'w') as f:
            json.dump(updated_recipe, f, indent=4, sort_keys=True)


def PicoBrewRecipeImport(recipe, rfid=None):
    r = {}
    r['id'] = uuid.uuid4().hex[:14] if rfid is None else rfid
    tmp = recipe.strip('#|').split('|')
    if len(tmp) > 1:
        r['image'] = tmp[1]
    tmp = tmp[0].split('/')
    steps = list(filter(None, tmp.pop().split(',')))
    r['name'] = ''.join(tmp)
    r['abv_tweak'] = steps.pop(0)
    r['ibu_tweak'] = steps.pop(0)
    r['abv'] = steps.pop(0)
    r['ibu'] = steps.pop(0)
    r['steps'] = []
    for step in [steps[i:i + 5] for i in range(0, len(steps), 5)]:
        s = {}
        s['temperature'] = int(step[0])
        s['step_time'] = int(step[1])
        s['drain_time'] = int(step[2])
        s['location'] = next(k for k, v in PICO_LOCATION.items() if v == step[3])
        s['name'] = step[4]
        r['steps'].append(s)
    filename = pico_recipe_path().joinpath('{}.json'.format(r['name'].replace(' ', '_')))
    if not filename.exists():
        with open(filename, "w") as file:
            json.dump(r, file, indent=4, sort_keys=True)
