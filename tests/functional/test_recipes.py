from app import create_app

flask_app = create_app('../../config.example.yaml')

def test_picobrew_recipes():
    """
    GIVEN a Flask application configured for testing
    WHEN the '/pico_recipes' page is requested (GET)
    THEN check that the response is valid
    """

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as test_client:
        response = test_client.get('/pico_recipes')
        assert response.status_code == 200
        assert b"<title>PicoBrew Server</title>" in response.data
        # html id for add/upload recipe
        assert b"recipe_actions" in response.data


def test_zymatic_recipes():
    """
    GIVEN a Flask application configured for testing
    WHEN the '/zymatic_recipes' page is requested (GET)
    THEN check that the response is valid
    """

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as test_client:
        response = test_client.get('/zymatic_recipes')
        assert response.status_code == 200
        assert b"<title>PicoBrew Server</title>" in response.data
        # html id for add/upload recipe
        assert b"recipe_actions" in response.data
        # verify server provided recipes are included in the UI (only in zymatic)
        assert b"Cleaning v1" in response.data
        assert b"New Clean Beta v6" in response.data
        assert b"Rinse v3" in response.data


def test_zseries_recipes():
    """
    GIVEN a Flask application configured for testing
    WHEN the '/zseries_recipes' page is requested (GET)
    THEN check that the response is valid
    """

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as test_client:
        response = test_client.get('/zseries_recipes')
        assert response.status_code == 200
        assert b"<title>PicoBrew Server</title>" in response.data
        # html id for add/upload recipe
        assert b"recipe_actions" in response.data
