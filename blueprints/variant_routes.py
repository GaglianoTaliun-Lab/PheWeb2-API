from flask import Blueprint, jsonify, g, request
from models import create_variant

bp = Blueprint('variant_routes', __name__)

@bp.route('/variant/<variant_code>/<stratification>', methods=['GET'])
def get_variant(variant_code, stratification):
    
    if 'variant' not in g:
        g.variant = create_variant()
    
    variant_phewas = g.variant.get_variant(variant_code, stratification)
        
    if variant_phewas:
        return jsonify(variant_phewas), 200
    else:
        return jsonify({"message": f"Cannot find variant with variant code {variant_code}."}), 404
    
    
@bp.route('/variant/stratification_list', methods=['GET'])
def get_stratifications_list():
    
    
    if 'variant' not in g:
        g.variant = create_variant()
        
    strat_list = g.variant.get_stratifications()
    
    if strat_list:
        return jsonify(strat_list), 200
    
    return jsonify({"message" : "Could not fetch the list of stratifications within data. Please check phenotypes.json file."}), 404

