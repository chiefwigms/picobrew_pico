import os
import tempfile

import pytest

from server import app


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_pico_recipes_page_successfully(client):
    """Retrieve /pico_recipes page successfully."""

    rv = client.get('/pico_recipes')
    assert '200' in rv.status


def test_zymatic_recipes_page_successfully(client):
    """Retrieve /zymatic_recipes page successfully."""

    rv = client.get('/zymatic_recipes')
    assert '200' in rv.status


def test_zseries_recipes_page_successfully(client):
    """Retrieve /zseries_recipes page successfully."""

    rv = client.get('/zseries_recipes')
    assert '200' in rv.status


def test_brew_history_page_successfully(client):
    """Retrieve /brew_history page successfully."""

    rv = client.get('/brew_history')
    assert '200' in rv.status


def test_ferm_history_page_successfully(client):
    """Retrieve /ferm_history page successfully."""

    rv = client.get('/ferm_history')
    assert '200' in rv.status