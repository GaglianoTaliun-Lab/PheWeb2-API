import os
from typing import List
import argparse
from flask import Flask
from flask_restx import Api
from preprocessing.blueprints import phenotype_routes, gene_routes, variant_routes, autocomplete
from flask_cors import CORS
from dotenv import load_dotenv
from .models.variant_utils import VariantLoading
from .models.autocomplete_util import AutocompleteLoading
load_dotenv()

app = Flask(__name__)
app.config.from_object("config")

CORS(app, origins=app.config["CORS_ORIGINS"])

# Create a central API object for Swagger documentation
api = Api(
    app,
    version="1.0",
    title="API Documentation",
    description="Swagger documentation for all API routes",
)

# Register blueprints with the shared API instance
api.add_namespace(phenotype_routes.api, path="/phenotypes")
api.add_namespace(gene_routes.api, path="/gene")
api.add_namespace(variant_routes.api, path="/variant")
api.add_namespace(autocomplete.api, path="/autocomplete")

def run(argv:List[str]) -> None:

    parser = argparse.ArgumentParser(prog = 'pheweb2 serve')
    parser.add_argument('--host', default = app.config["HOST"], help = f'The hostname to use to access PheWeb2 API. Default: {app.config["HOST"]}.')
    parser.add_argument('--port', type = int, default = app.config["PORT"], help = f'The port name to use to access PheWeb2 API. Default: {app.config["PORT"]}.')
    args = parser.parse_args(argv)

    # app.config["VARIANTS"] = VariantLoading(file_path=app.config["SITES_DIR"])
    with app.app_context():
        app.config["AUTOCOMPLETE"] = AutocompleteLoading(file_path=app.config["SITES_DIR"])

    
    app.run(
        host = args.host, port = args.port, debug = app.config['ENABLE_DEBUG']
    )


