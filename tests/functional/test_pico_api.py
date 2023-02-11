from app import create_app

flask_app = create_app('tests/functional/config.test.yaml')


def test_pico_c_firmware():
    """
    GIVEN a Flask application configured for testing
    WHEN the '/API/pico/getFirmware' API is requested (GET)
    THEN check that the firmware response is valid
    """

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as test_client:
        response = test_client.get('/API/pico/getFirmware?uid=unknown')
        assert response.status_code == 200
        # assert unknown device type doesn't get firmware loaded
        assert b"#F#" in response.data

        response = test_client.get('/API/pico/getFirmware?uid=picobrew_c_alt')
        assert response.status_code == 200
        # assert beginning of pico_c_0_1_34_alt.bin firmware file is in response
        assert b"#155864.0,72168d866990f8a46228df7113cb82ce|" in response.data
        
        response = test_client.get('/API/pico/getFirmware?uid=picobrew_c')
        assert response.status_code == 200
        # assert beginning of pico_c_0_1_34.bin firmware file is in response
        assert b"#156536.0,09a9cb94924d9023df6af18e4bed680f|" in response.data
