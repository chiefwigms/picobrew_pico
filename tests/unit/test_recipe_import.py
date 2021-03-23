from app.main.recipe_import import import_recipes, import_recipes_classic, ImportException
from app.main.config import MachineType
import unittest
import mock
from flask import Flask


# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, text, status_code):
            self.text = text
            self.status_code = status_code

    if args[0] == 'http://137.117.17.70/API/pico/getRecipe?uid=test&rfid=test_rfid&ibu=-1&abv=-1.0':
        return MockResponse("#good stuff#", 200)

    return MockResponse(args[0], 404)


class TestRecipeImport(unittest.TestCase):
    app = Flask('test')

    @mock.patch('app.main.recipe_import.import_recipes_classic')
    def test_calling_zymatic_import_function(self, mock_request):
        import_recipes('test', 'test', None, MachineType.ZYMATIC)
        mock_request.assert_called_once()

    @mock.patch('app.main.recipe_import.import_recipes_z')
    def test_zymatic_import_function(self, mock_request):
        import_recipes('test', 'test', None, MachineType.ZSERIES)
        mock_request.assert_called_once()

    @mock.patch('requests.get')
    def test_classic_fetch_failure_blank_response(self, mock_request):
        mock_request.text = ''
        with self.assertRaises(ImportException):
            import_recipes_classic('test', 'test', None, MachineType.ZYMATIC)
        mock_request.assert_called_once()

    @mock.patch('requests.get')
    def test_classic_fetch_failure_invalid_response(self, mock_request):
        mock_request.text = '#Invalid|#'
        with self.assertRaises(ImportException):
            import_recipes_classic('test', 'test', None, MachineType.ZYMATIC)
        mock_request.assert_called_once()

    @mock.patch('requests.get')
    def test_classic_fetch_failure_incomplete_response(self, mock_request):
        mock_request.text = '#'
        with self.assertRaises(ImportException):
            import_recipes_classic('test', 'test', None, MachineType.ZYMATIC)
        mock_request.assert_called_once()

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    @mock.patch('app.main.recipe_import.PicoBrewRecipeImport')
    def test_classic_fetch_success_complete_response(self, recipe_mocker, mock_request):
        recipe_mocker.return_value = None
        import_recipes_classic('test', 'test', 'test_rfid', MachineType.PICOBREW)
        mock_request.assert_called_once()
        recipe_mocker.assert_called_once()
        recipe_mocker.assert_called_with(recipe='#good stuff#', rfid='test_rfid')
