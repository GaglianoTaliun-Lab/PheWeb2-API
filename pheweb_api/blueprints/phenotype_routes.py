from flask import Blueprint, jsonify, g
from flask import current_app 
from ..models import create_phenotypes_list, create_tophits
from ..models.utils import extract_variants
from flask_restx import Namespace, Resource, reqparse
from ..conf import is_debug_mode
from .cache import cache

bp = Blueprint("phenotype_routes", __name__)
api = Namespace("phenotypes", description="Routes related to phenotypes")


class PhenotypeServiceNotAvailable(Exception):
    pass

class TopHitsServiceNotAvailable(Exception):
    pass

def get_pheno_service():
    if "pheno" not in g:
        g.pheno = create_phenotypes_list()
        if g.pheno is None:
            raise PhenotypeServiceNotAvailable(
                "Could not create phenotype service. Check if data path (named generated-by-pheweb/ by default) is correctly configured in .env or config.py."
            )
    return g.pheno

def get_tophits_service():
    if "tophits" not in g:
        g.tophits = create_tophits()
        if g.tophits is None:
            raise TopHitsServiceNotAvailable(
                "Could not create top hits service. Check if data path (named generated-by-pheweb/ by default) is correctly configured in .env or config.py."
            )
    return g.tophits


@api.route("/")
@api.route("/phenotypes_list")
@api.route("/<phenocode>/phenotypes_list")
class PhenotypeList(Resource):
    @cache.cached(timeout=300)
    def get(self, phenocode=None):
        try:
            current_app.logger.debug(f"Getting phenotypes list for {phenocode}")
            pheno_service = get_pheno_service()
            result = pheno_service.get_phenotypes_list(phenocode)
            if result:
                return result
            return {"data": [], "message": "Unsuccessfully retrieved list of phenotypes."}, 404
        except PhenotypeServiceNotAvailable as e:
            return {"message": str(e)}, 404
        except Exception as e:
            current_app.logger.error(f"Error getting phenotypes list for {phenocode}: {e}")
            return {"message": "Internal server error."}, 500


@api.route("/tophits")
class TopHits(Resource):
    @cache.cached(timeout=300)
    def get(self):
        try:
            current_app.logger.debug("Getting top hits")
            tophits_service = get_tophits_service()
            result = tophits_service.get_tophits()
            if result:
                return result
            return {"data": [], "message": "Unsuccessfully retrieved top hits."}, 404
        except TopHitsServiceNotAvailable as e:
            return {"message": str(e)}, 404
        except Exception as e:
            current_app.logger.error("Error getting top hits: {e}")
            return {"message": "Internal server error."}, 500


@api.route(
    "/interaction", doc={"description": "Retrieve all interaction result descriptions"}
)
@api.route(
    "/interaction_list",
    doc={"description": "Retrieve all interaction result descriptions"},
)
@api.route(
    "/<phenocode>/interaction_list",
    doc={
        "description": "Retrieve interaction result description(s) for specified phenocode"
    },
)
class InteractionList(Resource):
    def get(self, phenocode=None):
        try:
            current_app.logger.debug(f"Getting interaction list for {phenocode}")
            pheno_service = get_pheno_service()
            result = pheno_service.get_interaction_list(phenocode)
            if result:
                return jsonify(result)
            return {"data": [], "message": "Unsuccessfully retrieved list of interaction results."}, 404
        except PhenotypeServiceNotAvailable as e:
            return {"message": str(e)}, 404
        except Exception as e:
            current_app.logger.error(f"Error getting interaction list for {phenocode}: {e}")
            return {"message": "Internal server error."}, 500


@api.route("/<phenocode>/<stratification>/manhattan")
class Pheno(Resource):
    def get(self, phenocode, stratification=None):
        try:
            current_app.logger.debug(f"Getting pheno for {phenocode} and {stratification}")
            pheno_service = get_pheno_service()
            result = pheno_service.get_pheno(phenocode, stratification)
            return result
        except PhenotypeServiceNotAvailable as e:
            return {"message": str(e)}, 404
        except Exception as e:
            current_app.logger.error(f"Error getting pheno for {phenocode} and {stratification}: {e}")
            return {"message": "Internal server error."}, 500


parser = reqparse.RequestParser()
parser.add_argument("min_maf", type=float, default=0.0)
parser.add_argument("max_maf", type=float, default=0.5)
parser.add_argument("indel", type=str, default="both")


@api.route("/<string:phenocode>/<string:stratification>/filter")
class PhenoFilterSingle(Resource):
    @cache.cached(timeout=300)
    def get(self, phenocode, stratification=None):
        try:
            current_app.logger.debug(f"Getting pheno filter for {phenocode} and {stratification}")
            args = parser.parse_args()
            min_maf = args["min_maf"]
            max_maf = args["max_maf"]
            indel = args["indel"]

            data = extract_variants(phenocode, stratification, min_maf, max_maf, indel)
            return data
        except Exception as e:
            current_app.logger.error(f"Error getting pheno filter for {phenocode} and {stratification}: {e}")
            return {"message": "Internal server error."}, 500


@api.route("/<phenocode>/<stratification>/download")
class SumStats(Resource):
    def get(self, phenocode, stratification=None):
        try:
            current_app.logger.debug(f"Getting sum stats for {phenocode} and {stratification}")
            args = parser.parse_args()
            filtering_options = {
                "min_maf": args["min_maf"],
                "max_maf": args["max_maf"],
                "indel": args["indel"],
            }
            pheno_service = get_pheno_service()
            result = pheno_service.get_sumstats(phenocode, filtering_options, stratification)
            print(result)
            return result
        except PhenotypeServiceNotAvailable as e:
            return {"message": str(e)}, 404
        except Exception as e:
            current_app.logger.error(f"Error getting sum stats for {phenocode} and {stratification}: {e}")
            return {"message": "Internal server error."}, 500


@api.route("/<phenocode>/<stratification>/qq")
class QQ(Resource):
    def get(self, phenocode, stratification=None):
        try:
            current_app.logger.debug(f"Getting qq for {phenocode} and {stratification}")
            pheno_service = get_pheno_service()
            result = pheno_service.get_qq(phenocode, stratification)
            return result
        except PhenotypeServiceNotAvailable as e:
            return {"message": str(e)}, 404
        except Exception as e:
            current_app.logger.error(f"Error getting qq for {phenocode} and {stratification}: {e}")
            return {"message": "Internal server error."}, 500


@api.route("/<phenocode>/region/<region_code>")
@api.route("/<phenocode>/<stratification>/region/<region_code>")
class Region(Resource):
    @cache.cached(timeout=300)
    def get(self, phenocode, region_code, stratification=None):
        try:
            current_app.logger.debug(f"Getting region for {phenocode} and {stratification}")
            pheno_service = get_pheno_service()
            result = pheno_service.get_region(phenocode, stratification, region_code)
            if not result:
                return jsonify({
                    "data": [],
                    "message": f"Could not find region max pvalue data for phenocode={phenocode}, stratification={stratification}, region_code={region_code}"
                }), 404
            return jsonify(result)
        except PhenotypeServiceNotAvailable as e:
            return {"message": str(e)}, 404
        except Exception as e:
            current_app.logger.error(f"Error getting region for {phenocode} and {stratification}: {e}")
            return {"message": "Internal server error."}, 500


@api.route("/variants")
class MissingGWAS(Resource):
    @cache.cached(timeout=300)
    def post(self):
        try:
            current_app.logger.debug("Getting missing gwas")
            data = api.payload
            if not data:
                return {"message": "No data provided"}, 400

            pheno_service = get_pheno_service()
            results = pheno_service.get_gwas_missing(data)

            # process data using SNPFetcher            
            results = g.pheno.get_gwas_missing(data)
            processed_data = {
                "message": "success",
                "data": results,
            }
            return processed_data, 200
        except Exception as e:
            current_app.logger.error(f"Error getting missing gwas: {e}")
            return {"data": [], "message": "Internal server error."}, 500
