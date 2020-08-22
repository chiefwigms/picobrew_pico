from .recipe_import import import_recipes, import_recipes_classic
from .config import MachineType
import requests
from pytest_mock import MockerFixture
from unittest.mock import PropertyMock


def _mock_request(mocker: MockerFixture, body: str) -> MockerFixture:
    m = mocker.patch('requests.get')
    m.return_value = mocker.Mock(spec=requests.Response)
    txt = PropertyMock(return_value=body)
    type(m.return_value).text = txt
    return m

def test_routing(mocker) -> None:
    classic_mock = mocker.patch('app.main.recipe_import.import_recipes_classic')
    z_mock = mocker.patch('app.main.recipe_import.import_recipes_z')
    import_recipes('test', 'test', MachineType.ZYMATIC)
    import_recipes('test', 'test', MachineType.ZSERIES)
    classic_mock.assert_called_once()
    z_mock.assert_called_once()


def test_classic_fetch(mocker) -> None:
    get_mock = _mock_request(mocker, '')
    res = import_recipes_classic('test', 'test', MachineType.ZYMATIC)
    assert res == False
    get_mock.assert_called_once()

    get_mock = _mock_request(mocker, '#Invalid|#')
    res = import_recipes_classic('test', 'test', MachineType.ZYMATIC)
    get_mock.assert_called_once()
    assert res == False

    get_mock = _mock_request(mocker, '#')
    res = import_recipes_classic('test', 'test', MachineType.ZYMATIC)
    get_mock.assert_called_once()
    assert res == False

    get_mock = _mock_request(mocker, '#good stuff here#')
    import_mock = mocker.patch('app.main.recipe_import.PicoBrewRecipeImport')
    import_mock.return_value = None
    res = import_recipes_classic('test_machuid', 'test_accountid', MachineType.PICOBREW)
    get_mock.assert_called_once()
    import_mock.assert_called_once()
    import_mock.assert_called_with(recipe='#good stuff here#', rfid='test_accountid')
    assert res == True

    