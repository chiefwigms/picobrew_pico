import json
import uuid

from .config import zymatic_recipe_path, pico_recipe_path
from .model import PICO_LOCATION, ZYMATIC_LOCATION, ZSERIES_LOCATION


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
            self.location,
            self.drain_time
        )


class ZymaticRecipe():
    def __init__(self):
        self.id = None
        self.name = None
        self.name_ = None
        self.steps = []

    def parse(self, file):
        recipe = None
        with open(file) as f:
            recipe = json.load(f)
        self.id = recipe.get('id', 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX') or 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        self.name = recipe.get('name', 'Empty Recipe') or 'Empty Recipe'
        self.name_ = self.name.replace(" ", "_").replace("\'", "")
        if 'steps' in recipe:
            for recipe_step in recipe['steps']:
                step = ZymaticRecipeStep()
                step.name = recipe_step.get('name', 'Empty Step') or 'Empty Step'
                step.temperature = recipe_step.get('temperature', 70) or 70
                step.step_time = recipe_step.get('step_time', 0) or 0
                step.location = ZYMATIC_LOCATION[recipe_step.get('location', 'PassThru') or 'PassThru']
                step.drain_time = recipe_step.get('drain_time', 0) or 0
                self.steps.append(step)

    def serialize(self):
        steps = map(lambda step: step.serialize(), self.steps)
        return '{0}/{1}/{2}|'.format(
            self.name,
            self.id,
            ''.join(steps)
        )


def ZymaticRecipeImport(recipes):
    for recipe in recipes.strip('#|').split('|'):
        r = {}
        steps = list(filter(None, recipe.split('/')))
        r['name'] = steps.pop(0)
        r['id'] = steps.pop(0)
        r['steps'] = []
        for step in steps:
            values = step.split(',')
            s = {}
            s['name'] = values[0]
            s['temperature'] = values[1]
            s['step_time'] = values[2]
            s['location'] = next(k for k, v in ZYMATIC_LOCATION.items() if v == values[3])
            s['drain_time'] = values[4]
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
        return '{0},{1},{2},{3},{4}/'.format(
            self.name,
            self.temperature,
            self.step_time,
            self.location,
            self.drain_time
        )


class ZSeriesRecipe():
    def __init__(self):
        self.id = None
        self.name = None
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
        self.start_water = recipe.get('start_water', 13.1) or 13.1
        self.type_code = recipe.get('type_code', "Beer") or "Beer"
        if 'steps' in recipe:
            for recipe_step in recipe['steps']:
                step = ZSeriesRecipeStep()
                step.name = recipe_step.get('name', 'Empty Step') or 'Empty Step'
                step.temperature = recipe_step.get('temperature', 70) or 70
                step.step_time = recipe_step.get('step_time', 0) or 0
                step.location = ZSERIES_LOCATION[recipe_step.get('location', 'PassThru') or 'PassThru']
                step.drain_time = recipe_step.get('drain_time', 0) or 0
                self.steps.append(step)

    def serialize(self):
        r = {}
        r['ID'] = self.id
        r['Name'] = self.name
        r['StartWater'] = self.start_water
        r['Steps'] = []
        for step in self.steps:
            s = {}
            s['Name'] = step.name
            s['Location'] = step.location
            s['Temp'] = step.temperature
            s['Time'] = step.step_time
            s['Drain'] = step.drain_time
            r['Steps'].append(s)
        return r


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
            self.location,
            self.name
        )


class PicoBrewRecipe():
    def __init__(self):
        self.id = None
        self.name = None
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
        self.abv_tweak = recipe.get('abv_tweak', -1) or -1
        self.ibu_tweak = recipe.get('ibu_tweak', -1) or -1
        self.abv = recipe.get('abv', 6) or 6
        self.ibu = recipe.get('ibu', 40) or 40
        self.image = recipe.get('image', '') or ''
        if 'steps' in recipe:
            for recipe_step in recipe['steps']:
                step = PicoBrewRecipeStep()
                step.name = recipe_step.get('name', 'Empty Step') or 'Empty Step'
                step.location = PICO_LOCATION[recipe_step.get('location', 'PassThru') or 'PassThru']
                step.temperature = recipe_step.get('temperature', 70) or 70
                step.step_time = recipe_step.get('step_time', 0) or 0
                step.drain_time = recipe_step.get('drain_time', 0) or 0
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
        s['temperature'] = step[0]
        s['step_time'] = step[1]
        s['drain_time'] = step[2]
        s['location'] = next(k for k, v in PICO_LOCATION.items() if v == step[3])
        s['name'] = step[4]
        r['steps'].append(s)
    filename = pico_recipe_path().joinpath('{}.json'.format(r['name'].replace(' ', '_')))
    if not filename.exists():
        with open(filename, "w") as file:
            json.dump(r, file, indent=4, sort_keys=True)
