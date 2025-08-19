from flask import Flask
from models.variant_utils import VariantLoading
import os

def run(argv):
    app = Flask(__name__)
    app.config.from_object("config")  

    print(f"DEBUG: Loading variant data from {app.config['SITES_DIR']}")
    with app.app_context():
        VariantLoading(app.config["SITES_DIR"])
    print("DEBUG: Variant DB creation complete.")
