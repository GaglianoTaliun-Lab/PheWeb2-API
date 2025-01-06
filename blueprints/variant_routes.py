from flask import Blueprint, g
from models import create_variant
from flask_restx import Namespace, Resource

bp = Blueprint("variant_routes", __name__)
api = Namespace("variant", description="Routes related to variants")


@api.route("/<variant_code>/<stratification>")
class Variant(Resource):
    @api.doc(
        params={
            "variant_code": "Variant code string for the wanted variant, ex : 1-196698298-A-T",
            "stratification": "Stratification code, ex : European.Male ",
        }
    )
    def get(self, variant_code, stratification):
        """
        Get PheWAS plotting information for a given variant.
        """
        if "variant" not in g:
            g.variant = create_variant()

        variant_phewas = g.variant.get_variant(variant_code, stratification)

        if variant_phewas:
            return variant_phewas
        else:
            return {
                "message": f"Cannot find variant with variant code {variant_code}."
            }, 404


@api.route("/stratification_list")
class StratificationList(Resource):
    def get(self):
        """
        Get stratification information for PheWAS plot.
        """
        if "variant" not in g:
            g.variant = create_variant()

        strat_list = g.variant.get_stratifications()

        if strat_list:
            return strat_list, 200

        return {
            "message": "Could not fetch the list of stratifications within data. Please check phenotypes.json file."
        }, 404
