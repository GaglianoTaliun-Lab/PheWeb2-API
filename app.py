import os 
from flask import Flask
from blueprints import phenotype_routes, gene_routes, variant_routes
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object('config')

CORS(app, origins=app.config['CORS_ORIGINS'])

app.register_blueprint(phenotype_routes.bp)
app.register_blueprint(gene_routes.bp)
app.register_blueprint(variant_routes.bp)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9099))
    app.run(host='127.0.0.1', port=port, debug=True)
