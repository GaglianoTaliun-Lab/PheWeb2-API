from flask import Flask
from ..models.autocomplete_util import AutocompleteLoading
from ..conf import is_debug_mode
from ..file_utils import get_filepath
import os

SITES_DIR = get_filepath("sites", must_exist=False)


def run(argv):
    if is_debug_mode():
        print(f"DEBUG: Starting Autocomplete DB creation in {SITES_DIR}...")
    AutocompleteLoading()
    if is_debug_mode():
        print("DEBUG: Autocomplete DB creation complete.")
