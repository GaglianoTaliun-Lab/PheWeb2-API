import pytest
import pheweb_api.conf as conf
import os

config_filepath = os.path.join(conf.get_pheweb_base_dir(), "config.py")
if os.path.isfile(config_filepath):
    conf.load_overrides_from_file(config_filepath)

from pheweb_api.api_app import create_app

@pytest.fixture
def app():
    """
    Fixture for Flask test client with application context.
    """
    # Load config.py
    

    app = create_app(enable_cache=False)
    app.config.update({'TESTING': True})

    yield app

@pytest.fixture()
def client(app):
    return app.test_client()
