from flask import Blueprint, jsonify, g
from models import create_phenotypes, create_phenolist, create_variant

bp = Blueprint('phenotype_routes', __name__)

@bp.route('/hello')
def hello():
    return jsonify({'message': 'Hello, World!'})

@bp.route('/phenotypes', methods=['GET'])
def phenotype_table():
    
    if 'phenotypes' not in g:
        g.phenotypes = create_phenotypes()
        
    result = g.phenotypes.get_phenotypes()
    
    return result

@bp.route('/phenolist', defaults={'phenocode': None}, methods=['GET'])
@bp.route('/phenolist/<phenocode>', methods=['GET'])
def phenolist(phenocode):
    
    # cache pheno so to not load class more than once
    
    if 'pheno' not in g:
        pheno = create_phenolist()
        if not pheno:
            return jsonify({'message': 'Could not find phenolist file in given directory'}), 404
        g.pheno = pheno
        
    result = g.pheno.get_phenolist(phenocode)
    
    return result

@bp.route('/sumstats/<phenocode>', methods=['GET'])
def get_sumstats(phenocode):
    
    if 'pheno' not in g:
        g.pheno = create_phenolist()
        
    result = g.pheno.get_sumstats(phenocode)
    
    return result

@bp.route('/pheno/<phenocode>', methods=['GET'])
def get_pheno(phenocode):
    
    if 'pheno' not in g:
        g.pheno = create_phenolist()
        
    result = g.pheno.get_pheno(phenocode)
    
    # send from directory does all error coding automatically
    # but keeping this format in the likely case we change it in the future
    return result

@bp.route('/pheno-filter/<phenocode>', methods=['GET'])
def get_pheno_filter(phenocode):
    
    if 'pheno' not in g:
        g.pheno = create_phenolist()
        
    result = g.pheno.get_pheno_filtered(phenocode)
    return result

@bp.route('/qq/<phenocode>', methods=['GET'])
def get_qq(phenocode):
    
    if 'pheno' not in g:
        g.pheno = create_phenolist()
        
    result = g.pheno.get_qq(phenocode)
    
    return result

@bp.route('/variant/<variant_code>', methods=['GET'])
def get_variant(variant_code):
    
    if 'variant' not in g:
        g.variant = create_variant()
    
    variant_list = g.variant.get_variant(variant_code)
        
    if variant_list == []:
        return jsonify({"message": f"Cannot find variant with variant code {variant_code}."}), 404

    return jsonify(variant_list), 200