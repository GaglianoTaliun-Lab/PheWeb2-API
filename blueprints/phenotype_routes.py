from flask import Blueprint, jsonify
from models import Phenotypes, Variant, Pheno

bp = Blueprint('phenotype_routes', __name__)

@bp.route('/hello')
def hello():
    return jsonify({'message': 'Hello, World!'})

@bp.route('/phenotypes', methods=('GET'))
def phenotype_table():
    result = Phenotypes.get_phenotypes()
    
    if result == None:
        return jsonify({"message" : "Could not find phenotypes list. Please open an issue on GitHub"}), 404
    
    return jsonify(result), 200

@bp.route('/variant/<variant_code>', methods=('GET'))
def get_variant(variant_code):
    
    variant_list = Variant(variant_code).get_variant()
        
    if variant_list == []:
        return jsonify({"message": f"Cannot find variant with variant code {variant_code}."}), 404

    return jsonify(variant_list), 200

@bp.route('/pheno/<phenocode>', methods=('GET'))
def get_variant(variant_code):
    
    pheno_list = Pheno(phenocode).get_pheno()
        
    if pheno_list == []:
        return jsonify({"message": f"Cannot find variant with variant code {variant_code}."}), 404

    return jsonify(pheno_list), 200