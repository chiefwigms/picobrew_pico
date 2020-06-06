import json, uuid
from .. import *


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
        self.name_ = self.name.replace(" ", "_")
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
        filename = Path(ZYMATIC_RECIPE_PATH).joinpath('{}.json'.format(r['name'].replace(' ', '_')))
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
        default_image = '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffe000ffc01ffffc0000000000000003fff0003f601ff7ff0000000000000000fe7c00dff003de7f8000800030000000ff3e000ff801ff7f80078001fe000000dfbe000ff801feff80070001fe0000009c37000de000dffc0007803ffe0000021c070001c000cbf80007803ffe000000dcbf800dc0002ff0000780ffff000000fc9f800fc0003fe00007a3ffff800003fc1f800fc0000dc00007ffffff000003fc3f801dc0000fc00007f1f8bf000002bcb7800dc0000dc00007f0f9fffc00003c278001c00021c00007f079ff0600023c0f8021c00021c00007fe10fe0200003c1f8001c00021c00007e000ff00000c1c3f00c1c000c1c00007e080ff00000000fe0080600000600007e010ff00000ffffc00fff000fff00007e001ff00000ffff800fff800fff80007e001ff000007ffe0007ff8003ff80007f000fe00000000000000000000000007f001fe00fffe03fff003fffcfffbff87f001fe001fffc0ffff03fffcffffffc7e0007e00cfff633c3f807e3e1cfdede7e0017e006fffb13f9fc03f9f3dfdefe7e0017e000ffff8bfefc03fdf3cffe7e7e0017e0007eef8b7ffe037df1cfdf787f0017e0001e6bc87a7e0073f18f8ff07f0017e0005cc3c841bf02fbf1aefff07f8dffe02070d7c3c3ff030df1e4ece07fdffff8c24067c303fe0ffe00e0e4e07fdffff003df778f79bc0ffe00f1f0e07fddffe010dff30bfcdf0afec0f1f0e07fc08ff7015fd38afedb82fce0f1e1e07fffffe0001e4388f21bc8f0f061e1c07fffffc0001e03c8f203c0f4f061e1c07e0017c0061f07f07003d078f063e1c07c0003e000000fe01987c000f033f1c03e0007c00ffffffffcfffffff03fff800ff9ff000fffffbffeffbffff03fbf800000000007fffe1ffe3f1ffff00f9f800000000001fff00ffc0c0fffe007070000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
        recipe = None
        with open(file) as f:
            recipe = json.load(f)
        self.id = recipe.get('id', 'XXXXXXXXXXXXXX') or 'XXXXXXXXXXXXXX'
        self.name = recipe.get('name', 'Empty Recipe') or 'Empty Recipe'
        self.name_ = self.name.replace(" ", "_")
        self.abv_tweak = recipe.get('abv_tweak', -1) or -1
        self.ibu_tweak = recipe.get('ibu_tweak', -1) or -1
        self.abv = recipe.get('abv', 6) or 6
        self.ibu = recipe.get('ibu', 40) or 40
        self.image = recipe.get('image', default_image) or default_image
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
    r['image'] = tmp[1]
    tmp = tmp[0].split('/')
    r['name'] = tmp[0]
    steps = list(filter(None, tmp[1].split(',')))
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
    filename = Path(PICO_RECIPE_PATH).joinpath('{}.json'.format(r['name'].replace(' ', '_')))
    if not filename.exists():
        with open(filename, "w") as file:
            json.dump(r, file, indent=4, sort_keys=True)
