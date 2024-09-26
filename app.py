from os import getenv
from flask import Flask
from blueprints import phenotype_routes
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object('config')

CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)

app.register_blueprint(phenotype_routes.bp, url_prefix='/ui')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9099)
