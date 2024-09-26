from flask import Blueprint, jsonify, make_response
from models import phenotypes

bp = Blueprint('phenotype_routes', __name__)

@bp.route('/hello')
def hello():
    return jsonify({'message': 'Hello, World!'})

@bp.route('/phenotypes')
def phenotype_table():
    result = phenotypes.get_phenotypes()
    
    return make_response(jsonify(result), 200)


