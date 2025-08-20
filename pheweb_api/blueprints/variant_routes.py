from flask import g
from ..models import create_variant
from flask_restx import Namespace, Resource
import logging

api = Namespace("variant", description="Routes related to variants")

class VariantServiceNotAvailable(Exception):
    pass

def get_variant_service():
    if "variant" not in g:
        g.variant = create_variant()
        if g.variant is None:
            raise VariantServiceNotAvailable(
                "Could not create variant service. Check if data path (named generated-by-pheweb/ by default) is correctly configured in .env or config.py."
            )
    return g.variant

@api.route("/<variant_code>/<stratification>")
class Variant(Resource):
    @api.doc(
        params={
            "variant_code": "Variant code string for the wanted variant, ex: 1-196698298-A-T",
            "stratification": "Stratification code, ex: European.Male",
        }
    )
    def get(self, variant_code, stratification):
        try:
            variant_service = get_variant_service()
            variant_phewas = variant_service.get_variant(variant_code, stratification)

            if variant_phewas:
                return variant_phewas, 200
            return {"message": f"Variant '{variant_code}' not found."}, 404

        except VariantServiceNotAvailable as e:
            return {"message": str(e)}, 404
        except Exception as e:
            logging.exception("Unexpected error in /variant endpoint")
            return {"message": "Internal server error."}, 500

# TODO: remove stratification list endpoint and category list endpoint from variant routes
@api.route("/stratification_list")
class StratificationList(Resource):
    def get(self):
        try:
            variant_service = get_variant_service()
            strat_list = variant_service.get_stratifications()

            if strat_list:
                return strat_list, 200
            return {"message": "Stratification list not found."}, 404

        except VariantServiceNotAvailable as e:
            return {"message": str(e)}, 404
        except Exception:
            logging.exception("Error in /stratification_list")
            return {"message": "Internal server error."}, 500

@api.route("/category_list")
class CategoryList(Resource):
    def get(self):
        try:
            variant_service = get_variant_service()
            cat_list = variant_service.get_categories()

            if cat_list:
                return cat_list, 200
            return {"message": "Category list not found."}, 404

        except VariantServiceNotAvailable as e:
            return {"message": str(e)}, 404
        except Exception:
            logging.exception("Error in /category_list")
            return {"message": "Internal server error."}, 500

@api.route("/rsid/<variant_code>")
class Rsid(Resource):
    def get(self, variant_code):
        try:
            variant_service = get_variant_service()
            rsid = variant_service.get_variant_rsid(variant_code)
            return rsid, 200
        except VariantServiceNotAvailable as e:
            return {"message": str(e)}, 404
        except Exception:
            logging.exception("Error in /rsid endpoint")
            return {"message": "Internal server error."}, 500

@api.route("/nearest_genes/<variant_code>")
class NearestGenes(Resource):
    def get(self, variant_code, stratification="european.male"):
        try:
            variant_service = get_variant_service()
            nearest_genes = variant_service.get_nearest_genes(variant_code)
            return nearest_genes, 200
        except VariantServiceNotAvailable as e:
            return {"message": str(e)}, 404
        except Exception:
            logging.exception("Error in /nearest_genes endpoint")
            return {"message": "Internal server error."}, 500
