from flask import Blueprint, jsonify, g, request
from models import create_phenotypes, create_phenolist, create_variant, create_tophits, create_genes
from utils import extract_variants


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


@bp.route('/tophits', methods=['GET'])
def tophits_table():
    
    if 'tophits' not in g:
        g.tophits = create_tophits()
        
    result = g.tophits.get_tophits()
    
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

@bp.route('/pheno-filter/<phenocode1>', methods=['GET'])
@bp.route('/pheno-filter/<phenocode1>/<phenocode2>', methods=['GET'])
def get_pheno_filter(phenocode1, phenocode2 = None):
    
    # this will get optional parameters after a '?', such as /pheno-filter/DIA_TYPE2_COM.European.Male/DIA_TYPE1_COM.European.Female?min_maf=0.1&min_maf=0.2
    min_maf = request.args.get('min_maf', default=0.0, type=float)
    max_maf = request.args.get('max_maf', default=0.5,type=float)
    indel = request.args.get('indel', default="both", type=str)
    #csq = request.args.get('csq', default='', type=str)
    
    # TODO : we can cache the BEST_OF_PHENO_DIR/<phenocode> for better performance after 1 filter
    # TODO : also, move extract variants call to models.py
    
    chosen_variants1 : list = extract_variants(phenocode1, min_maf, max_maf, indel)
    chosen_variants2 : list = extract_variants(phenocode2, min_maf, max_maf, indel) if phenocode2 else None
    
    data = []
    data.append(chosen_variants1)
    
    if chosen_variants2:
        data.append(chosen_variants2)

    return jsonify(data), 200

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