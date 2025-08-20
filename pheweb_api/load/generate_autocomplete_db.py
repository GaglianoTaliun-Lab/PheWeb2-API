from flask import Flask
from ..models.autocomplete_util import AutocompleteLoading
from ..conf import is_debug_mode, get_pheweb_data_dir
import os

SITES_DIR = os.path.join(get_pheweb_data_dir(), "sites")

def run(argv):
    app = Flask(__name__)
    app.config.from_object("config")  
    if is_debug_mode(): print(f"DEBUG: Starting Autocomplete DB creation in {SITES_DIR}...")
    AutocompleteLoading(SITES_DIR)
    if is_debug_mode(): print("DEBUG: Autocomplete DB creation complete.")
