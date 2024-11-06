from flask import Blueprint, jsonify, g, request

bp = Blueprint('variant_routes', __name__)

@bp.route('/variant/<variant_code>', methods=['GET'])
def get_variant(variant_code):
    
    if 'variant' not in g:
        g.variant = create_variant()
    
    variant_list = g.variant.get_variant(variant_code)
        
    if variant_list == []:
        return jsonify({"message": f"Cannot find variant with variant code {variant_code}."}), 404

    return jsonify(variant_list), 200