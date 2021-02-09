import os
import tempfile

import pytest

from server import app


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_root_page_successfully(client):
    """Retrieve root page successfully."""

    rv = client.get('/')
    assert '200' in rv.status