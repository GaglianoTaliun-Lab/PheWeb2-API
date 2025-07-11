from flask import Flask
from models.variant_utils import VariantLoading
from models.autocomplete_util import AutocompleteLoading
import os

def run(argv):
    app = Flask(__name__)
    app.config.from_object("config")  

    print(f"DEBUG: Loading variant data from {app.config['SITES_DIR']}")
    with app.app_context():
        AutocompleteLoading(app.config["SITES_DIR"])
    print("DEBUG: Autocomplete DB creation complete.")
