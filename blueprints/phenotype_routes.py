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
@api.route(
    "/phenotypes_list/<phenocode>",
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
            return jsonify(result)
        else:
            # TODO : specify which phenocode?
            return jsonify(
                {"data": [], "message": "Unsuccesfully retrieved list of phenotypes."}
            ), 404


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
@api.route(
    "/interaction_list/<phenocode>",
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
            return jsonify(
                {
                    "data": [],
                    "message": "Unsuccesfully retrieved list of interaction results.",
                }
            ), 404


# this is the 'hidden' sumstats download api
@api.route("/sumstats/<phenocode>")
@api.hide
class SumStats(Resource):
    @api.doc(
        params={
            "phenocode": 'Phenocode string for the first trait. Ex: "DIA_TYPE2_COM.European.Male"',
        }
    )
    def get(self, phenocode):
        """
        Retrieve summary stats information for a specified phenotype.
        """
        if "pheno" not in g:
            g.pheno = create_phenotypes_list()

        result = g.pheno.get_sumstats(phenocode)

        return result


@api.route(
    "/<phenocode>",
    doc={
        "description": "Retrieve pheno plotting and table information for a particular phenocode (used for pheno page)"
    },
)
class Pheno(Resource):
    @api.doc(
        params={
            "phenocode": 'Phenocode string for the first trait. Ex: "DIA_TYPE2_COM.European.Male"',
        }
    )
    def get(self, phenocode):
        """
        Retrieve pheno plotting and table information for a particular phenocode (used for pheno page)
        """
        if "pheno" not in g:
            g.pheno = create_phenotypes_list()

        result = g.pheno.get_pheno(phenocode)

        # send from directory does all error coding automatically
        # but keeping this format in the likely case we change it in the future
        return result


parser = reqparse.RequestParser()
parser.add_argument("min_maf", type=float, default=0.0, help="Minimum MAF value")
parser.add_argument("max_maf", type=float, default=0.5, help="Maximum MAF value")
parser.add_argument(
    "indel", type=str, default="both", help="Type of variants (e.g., indel, snp, both)"
)

@api.route("/pheno-filter/<string:phenocode1>")
@api.route("/pheno-filter/<string:phenocode1>/<string:phenocode2>")
class PhenoFilter(Resource):
    @api.doc(
        params={
            "phenocode1": 'Phenocode string for the first trait. Ex: "DIA_TYPE2_COM.European.Male"',
            "phenocode2": 'Phenocode string for the second trait (optional). Ex: "DIA_TYPE1_COM.European.Female"',
        }
    )
    def get(self, phenocode1, phenocode2=None):
        """
        Retrieve filtered variants for the specified phenocode(s).
        """
        args = parser.parse_args()
        min_maf = args["min_maf"]
        max_maf = args["max_maf"]
        indel = args["indel"]

        # Extract variants for the phenocodes
        chosen_variants1 = extract_variants(phenocode1, min_maf, max_maf, indel)
        chosen_variants2 = (
            extract_variants(phenocode2, min_maf, max_maf, indel)
            if phenocode2
            else None
        )

        data = [chosen_variants1]
        if chosen_variants2:
            data.append(chosen_variants2)

        return jsonify(data), 200


@api.route("/qq/<phenocode>")
class QQ(Resource):
    @api.doc(
        params={
            "phenocode": 'Phenocode string for the wanted trait. Ex: "DIA_TYPE2_COM.European.Male"',
        }
    )
    def get(self, phenocode):
        """
        Retrieve qq results for the specified phenocode(s).
        """
        if "pheno" not in g:
            g.pheno = create_phenotypes_list()

        result = g.pheno.get_qq(phenocode)

        return result


@api.route("/<phenocode>/region/<region_code>")
class Region(Resource):
    @api.doc(
        params={
            "phenocode": 'Phenocode string for the wanted trait. Ex: "DIA_TYPE2_COM.European.Male"',
            "region_code": 'Region code string formatted as such : "1:20000-100000" ',
        }
    )
    def get(self, phenocode, region_code):
        """
        Get region plotting data for LocusZoom region plots.
        """
        if "pheno" not in g:
            g.pheno = create_phenotypes_list()

        result = None

        result = g.pheno.get_region(phenocode, region_code)
        if not result:
            # TODO : did we fail to get the phenocode or the region?
            return jsonify(
                {
                    "data": [],
                    "message": f"Could not find region data for {phenocode=} and {region_code=}",
                }
            ), 404

        return jsonify(result)

@api.route('/gwas.missing')
class MissingGWAS(Resource):
    @api.response(400, 'Bad Request')
    @api.response(500, 'Internal Server Error')
    def post(self):
        """Process missing GWAS data for specific stratifications"""
        try:
            data = api.payload  # Using api.payload to access the incoming JSON data
            if not data:
                return {'message': 'No data provided'}, 400
            
            if 'pheno' not in g:
                g.pheno = create_phenotypes_list()
                
            # process data using SNPFetcher
            results = g.pheno.get_gwas_missing(data)
            
            # Debugging prints to console
            print("input")
            for key, snp_list in data.items():
                print(f"{key}: {len(snp_list)} elements")
            print("\noutput")
            for key, snp_list in results.items():
                print(f"{key}: {len(snp_list)} elements")
            
            processed_data = {
                "message": "success",
                "data": results,
            }
            return processed_data, 200
        except Exception as e:
            return {'data': [], "message": str(e)}, 500