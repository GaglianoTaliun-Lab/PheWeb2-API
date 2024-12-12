from flask import Blueprint, jsonify, g
from models import create_phenotypes_list, create_tophits
from models.utils import extract_variants
from flask_restx import Namespace, Resource, reqparse

bp = Blueprint("phenotype_routes", __name__)
api = Namespace("phenotypes", description="Routes related to phenotypes")


@api.route("/", doc={"description": "Retrieve the all phenotype descriptions"})
@api.route(
    "/phenotypes_list", doc={"description": "Retrieve the all phenotype descriptions"}
)
# @api.route( #TODO : remove this for consistency
#     "/phenotypes_list/<phenocode>",
#     doc={"description": "Retrieve all phenotype descriptions for specified phenocode"},
# )
@api.route(
    "/<phenocode>/phenotypes_list",
    doc={"description": "Retrieve all phenotype descriptions for specified phenocode"},
)
class PhenotypeList(Resource):
    @api.doc(responses={200: "Success", 404: "Could not retrieve list of phenotypes"})
    def get(self, phenocode=None):
        """
        Retrieve phenotype meta information
        """
        # cache pheno so to not load class more than once
        if "pheno" not in g:
            g.pheno = create_phenotypes_list()

        result = g.pheno.get_phenotypes_list(phenocode)
        if result:
            return result
        else:
            # TODO : specify which phenocode?
            return {"data": [], "message": "Unsuccesfully retrieved list of phenotypes."}


@api.route(
    "/tophits",
    doc={"description": "Retrieve 1000 top variants (1 per loci) for all the GWAS"},
)
class TopHits(Resource):
    def get(self):
        """
        Retrieve 1000 top variants (1 per loci) for all the GWAS
        """
        if "tophits" not in g:
            g.tophits = create_tophits()

        result = g.tophits.get_tophits()

        return result


@api.route(
    "/interaction", doc={"description": "Retrieve all interaction result descriptions"}
)
@api.route(
    "/interaction_list",
    doc={"description": "Retrieve all interaction result descriptions"},
)
# @api.route( #TODO: remove this for consistency
#     "/interaction_list/<phenocode>",
#     doc={
#         "description": "Retrieve interaction result description(s) for specified phenocode"
#     },
# )
@api.route(
    "/<phenocode>/interaction_list",
    doc={
        "description": "Retrieve interaction result description(s) for specified phenocode"
    },
)
class InteractionList(Resource):
    def get(self, phenocode=None):
        """
        Retrieve interaction result meta information
        """

        # cache pheno so to not load class more than once
        if "pheno" not in g:
            g.pheno = create_phenotypes_list()

        result = g.pheno.get_interaction_list(phenocode)
        if result:
            return jsonify(result)
        else:
            return {
                        "data": [],
                        "message": "Unsuccesfully retrieved list of interaction results.",
                    }


# this is the 'hidden' sumstats download api
#@api.route("/sumstats/<phenocode>")
@api.route("/<phenocode>/<stratification>/download")
class SumStats(Resource):
    @api.doc(
        params={
            "phenocode": 'Phenocode string for the first trait. Ex: "DIA_TYPE2_COM"',
            "stratification" : "Stratification string for the given phenocode. Ex: .European.Male"
        }
    )
    def get(self, phenocode, stratification = None):
        """
        Retrieve summary stats information for a specified phenotype.
        """
        if "pheno" not in g:
            g.pheno = create_phenotypes_list()
            
        result = g.pheno.get_sumstats(phenocode, stratification)

        return result


# @api.route( # TODO: remove this!
#     "/<phenocode>",
#     doc={
#         "description": "Retrieve pheno plotting and table information for a particular phenocode (used for pheno page)"
#     },
# )
@api.route(
    "/<phenocode>/<stratification>",
    doc={
        "description": "Retrieve pheno plotting and table information for a particular phenocode and stratification (used for pheno page)"
    },
)
class Pheno(Resource):
    @api.doc(
        params={
            "phenocode": 'Phenocode string for the first trait. Ex: "DIA_TYPE2_COM"',
            "stratification" : "Stratification string for the given phenocode. Ex: .European.Male"
        }
    )
    def get(self, phenocode, stratification = None):
        """
        Retrieve pheno plotting and table information for a particular phenocode (used for pheno page)
        """
        if "pheno" not in g:
            g.pheno = create_phenotypes_list()

        result = g.pheno.get_pheno(phenocode, stratification)
        
        # send from directory does all error coding automatically
        # but keeping this format in the likely case we change it in the future
        return result


parser = reqparse.RequestParser()
parser.add_argument("min_maf", type=float, default=0.0, help="Minimum MAF value")
parser.add_argument("max_maf", type=float, default=0.5, help="Maximum MAF value")
parser.add_argument(
    "indel", type=str, default="both", help="Type of variants (e.g., indel, snp, both)"
)

# # TODO: remove this whole class and API endpoints.
# @api.route("/pheno-filter/<string:phenocode1>") # TODO: remove this for consistency
# @api.route("/pheno-filter/<string:phenocode1>/<string:phenocode2>") # TODO: remove this because it should only be one route at a time.
# class PhenoFilter(Resource):
#     @api.doc(
#         params={
#             "phenocode1": 'Phenocode string for the first trait. Ex: "DIA_TYPE2_COM.European.Male"',
#             "phenocode2": 'Phenocode string for the second trait (optional). Ex: "DIA_TYPE1_COM.European.Female"',
#         }
#     )
#     def get(self, phenocode1, phenocode2=None):
#         """
#         Retrieve filtered variants for the specified phenocode(s).
#         """
#         args = parser.parse_args()
#         min_maf = args["min_maf"]
#         max_maf = args["max_maf"]
#         indel = args["indel"]

#         # Extract variants for the phenocodes
#         chosen_variants1 = extract_variants(phenocode1, min_maf, max_maf, indel)
#         chosen_variants2 = (
#             extract_variants(phenocode2, min_maf, max_maf, indel)
#             if phenocode2
#             else None
#         )

#         data = [chosen_variants1]
#         if chosen_variants2:
#             data.append(chosen_variants2)

#         return data, 200

@api.route("/<string:phenocode>/<string:stratification>/filter")
class PhenoFilterSingle(Resource):
    @api.doc(
        params={
            "phenocode": 'Phenocode string for the first trait. Ex: "DIA_TYPE2_COM"',
            "stratification" : "Stratification string for the given phenocode. Ex: .European.Male"
        }
    )
    def get(self, phenocode, stratification = None):
        """
        Retrieve filtered variants for the specified phenocode(s).
        """
        args = parser.parse_args()
        min_maf = args["min_maf"]
        max_maf = args["max_maf"]
        indel = args["indel"]

        # Extract variants for the phenocodes
        chosen_variants = extract_variants(phenocode, stratification, min_maf, max_maf, indel)

        data = chosen_variants

        return data


# @api.route("/qq/<phenocode>") # TODO: remove this for consistency
@api.route("/<phenocode>/<stratification>/qq")
class QQ(Resource):
    @api.doc(
        params={
            "phenocode": 'Phenocode string for the first trait. Ex: "DIA_TYPE2_COM"',
            "stratification" : "Stratification string for the given phenocode. Ex: European.Male"
        }
    )
    def get(self, phenocode, stratification = None):
        """
        Retrieve qq results for the specified phenocode(s).
        """
        if "pheno" not in g:
            g.pheno = create_phenotypes_list()

        result = g.pheno.get_qq(phenocode, stratification)

        return result


# @api.route("/<phenocode>/region/<region_code>") #TODO : remove this for consistency
@api.route("/<phenocode>/region/<region_code>")
@api.route("/<phenocode>/<stratification>/region/<region_code>")
class Region(Resource):
    @api.doc(
        params={
            "phenocode": 'Phenocode string for the wanted trait. Ex: "DIA_TYPE2_COM"',
            "stratification" : "Stratification string for the given phenocode. Ex: European.Male",
            "region_code": 'Region code string formatted as such : "1:20000-100000" ',
        }
    )
    def get(self, phenocode,  region_code, stratification = None):
        """
        Get region plotting data for LocusZoom region plots.
        """
        if "pheno" not in g:
            g.pheno = create_phenotypes_list()

        result = None

        result = g.pheno.get_region(phenocode, stratification, region_code)
        if not result:
            # TODO : did we fail to get the phenocode or the region?
            return jsonify(
                {
                    "data": [],
                    "message": f"Could not find region data for {phenocode=}, {stratification=} and {region_code=}",
                }
            ), 404

        return jsonify(result)
