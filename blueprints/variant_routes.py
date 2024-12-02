from flask import Blueprint, jsonify, g, request
from models import create_variant
from flask import Blueprint
from flask_restx import Namespace, Resource, reqparse

bp = Blueprint('variant_routes', __name__)
api = Namespace('variant', description="Routes related to variants")

@api.route('/variant/<variant_code>/<stratification>')
class Variant(Resource):
    @api.doc(params={
        'variant_code': 'Variant code string for the wanted variant, ex : 1-100000-A-T',
        'stratification': 'Stratification code, ex : European.Male ',
    })
    def get(self, variant_code, stratification):
        """
        Get PheWAS plotting information for a given variant.
        """
        if 'variant' not in g:
            g.variant = create_variant()
        
        variant_phewas = g.variant.get_variant(variant_code, stratification)
            
        if variant_phewas:
            return jsonify(variant_phewas), 200
        else:
            return jsonify({"message": f"Cannot find variant with variant code {variant_code}."}), 404
        
@api.route('/variant/stratification_list')
class StratificationList(Resource):
    def get(self):
        """
        Get stratification information for PheWAS plot.
        """
        if 'variant' not in g:
            g.variant = create_variant()
            
        strat_list = g.variant.get_stratifications()
        
        if strat_list:
            return jsonify(strat_list), 200
        
        return jsonify({"message" : "Could not fetch the list of stratifications within data. Please check phenotypes.json file."}), 404
    