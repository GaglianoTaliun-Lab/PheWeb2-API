import os
from flask import Flask
from flask_restx import Api
from blueprints import phenotype_routes, gene_routes, variant_routes, autocomplete
from flask_cors import CORS
from dotenv import load_dotenv
from models.variant_utils import VariantLoading
from models.autocomplete_util import AutocompleteLoading
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

def main():
    # app.config["VARIANTS"] = VariantLoading(file_path=app.config["SITES_DIR"])
    with app.app_context():
        app.config["AUTOCOMPLETE"] = AutocompleteLoading(file_path=app.config["SITES_DIR"])

    
    app.run(
        host = app.config["HOST"], port = app.config["PORT"], debug = app.config['ENABLE_DEBUG']
    )

if __name__ == "__main__":
    main()

