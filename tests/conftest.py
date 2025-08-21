import pytest
import pheweb_api.conf as conf
from pheweb_api.api_app import create_app
import os

@pytest.fixture
def app():
    """
    Fixture for Flask test client with application context.
    """
    app = create_app(enable_cache=False)
    app.config.update({'TESTING': True})

    # Load config.py
    config_filepath = os.path.join(conf.get_pheweb_base_dir(), "config.py")
    if os.path.isfile(config_filepath):
        conf.load_overrides_from_file(config_filepath)

    yield app

@pytest.fixture()
def client(app):
    return app.test_client()
