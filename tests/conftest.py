from pathlib import Path

import pytest

FIXTURE_PATH = Path(__file__).parent / 'fixtures'
APP_PATH = FIXTURE_PATH / 'testapp'


@pytest.fixture
def fixture_path():
    return FIXTURE_PATH


@pytest.fixture
def app_path():
    return APP_PATH
