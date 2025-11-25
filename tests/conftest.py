import os
import pytest


@pytest.fixture(scope='session')
def base_url():
    return os.getenv('BASE_URL', 'http://localhost:3000')


@pytest.fixture(scope='session')
def admin_token():
    return os.getenv('ADMIN_TOKEN')
