from flask import Blueprint, jsonify, g, request, json
from models import create_phenotypes_list, create_tophits
from models.utils import extract_variants

from flask_restx import fields, Resource, Api

bp = Blueprint('phenotype_routes', __name__)

api = Api(bp)
# @bp.route('/phenotypes', methods=['GET'])
# def phenotype_list():
    
#     # cache pheno so to not load class more than once    
#     if 'pheno' not in g:
#         g.pheno = create_phenotypes_list()
        
#     result = g.pheno.get_phenotypes_list()
    
#     return result

# @bp.route('/phenotypes/interaction', methods=['GET'])
# def interaction_list():
    
#     # cache pheno so to not load class more than once    
#     if 'pheno' not in g:
#         g.pheno = create_phenotypes_list()
        
#     result = g.pheno.get_interaction_list()
    
#     return result

@api.route('/phenotypes/tophits', doc={
    'description': "Retrieve 1000 top variants (1 per loci) for all the GWAS"
})
class TopHits(Resource):
    def get(self):
        if 'tophits' not in g:
            g.tophits = create_tophits()
            
        result = g.tophits.get_tophits()
        
        return result

@api.route('/phenotypes/phenotypes_list', doc={
    'description': "Retrieve the all phenotype descriptions"
})
@api.route('/phenotypes/phenotypes_list/<phenocode>', doc={
    'description': "Retrieve all phenotype descriptions for specified phenocode"
})
@api.doc(params={'phenocode': 'Phenocode string for wanted trait. Ex : "DIA_TYPE2_COM"'})
class PhenotypeList(Resource):
    @api.doc(responses={
        200: 'Success',
        404: 'Could not retrieve list of phenotypes'
    })
    def get(self, phenocode = None):
        # cache pheno so to not load class more than once    
        if 'pheno' not in g:
            g.pheno = create_phenotypes_list()
        
        result = g.pheno.get_phenotypes_list(phenocode)
        if result:
            return jsonify(result)
        else:
            # TODO : specify which phenocode?
            return jsonify({'data' : [], 'message' : f"Unsuccesfully retrieved list of phenotypes."}), 404
    
@bp.route('/phenotypes/interaction_list', methods=['GET'])
@bp.route('/phenotypes/interaction_list/<phenocode>', methods=['GET'])
def interaction_list(phenocode = None):
    
    # cache pheno so to not load class more than once    
    if 'pheno' not in g:
        g.pheno = create_phenotypes_list()
    
    result = g.pheno.get_interaction_list(phenocode)
    if result:
        return jsonify(result)
    else:
        return jsonify({'data' : [], 'message' : f"Unsuccesfully retrieved list of interaction results."}), 404
    
@bp.route('/phenotypes/sumstats/<phenocode>', methods=['GET'])
def get_sumstats(phenocode):
    
    if 'pheno' not in g:
        g.pheno = create_phenotypes_list()
        
    result = g.pheno.get_sumstats(phenocode)
    
    return result

@bp.route('/phenotypes/<phenocode>', methods=['GET'])
def get_pheno(phenocode):
    
    if 'pheno' not in g:
        g.pheno = create_phenotypes_list()
        
    result = g.pheno.get_pheno(phenocode)
    
    # send from directory does all error coding automatically
    # but keeping this format in the likely case we change it in the future
    return result

@bp.route('/phenotypes/pheno-filter/<phenocode1>', methods=['GET'])
@bp.route('/phenotypes/pheno-filter/<phenocode1>/<phenocode2>', methods=['GET'])
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

@bp.route('/phenotypes/qq/<phenocode>', methods=['GET'])
def get_qq(phenocode):
    
    if 'pheno' not in g:
        g.pheno = create_phenotypes_list()
        
    result = g.pheno.get_qq(phenocode)
    
    return result

@bp.route('/phenotypes/<phenocode>/region/<region_code>', methods=['GET'])
def get_region(phenocode,region_code):
    
    if 'pheno' not in g:
        g.pheno = create_phenotypes_list()
        
    result = None
    
    print(phenocode, region_code)
    result = g.pheno.get_region(phenocode, region_code)
    if not result:
        # TODO : did we fail to get the phenocode or the region?
        return jsonify({'data' : [], 'message' : f"Could not find region data for {phenocode=} and {region_code=}"}), 404
        
    return jsonify(result)