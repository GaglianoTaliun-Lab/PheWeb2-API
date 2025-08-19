from flask import Blueprint, g
from ..models import create_genes
from flask_restx import Namespace, Resource

bp = Blueprint("gene_routes", __name__)
api = Namespace("gene", description="Routes related to genes")

class GenesServiceNotAvailable(Exception):
    pass

def get_genes_service():
    if "genes" not in g:
        g.genes = create_genes()
        if g.genes is None:
            raise GenesServiceNotAvailable(
                "Could not create gene service. Check if data path (named generated-by-pheweb/ by default) is correctly configured in .env or config.py."
            )
    return g.genes

@api.route("/<gene>")
class SignificantAssociationTable(Resource):
    def get(self, gene):
        """
        Get association information for a specific gene.
        """
        try:
            genes_service = get_genes_service()
            table_data = genes_service.get_genes_table(gene)

            if table_data:
                return table_data, 200
            else:
                return {"data": [], "message": "No data found for this gene"}, 404

        except GenesServiceNotAvailable as e:
            return {"message": str(e)}, 404
        except Exception as e:
            return {"message": "Internal server error."}, 500


@api.route("/<gene>/gene_position")
class GenePosition(Resource):
    def get(self, gene):
        """
        Get base-pair and chromosome position of a given gene
        """
        try:
            genes_service = get_genes_service()
            chrom, start, end = genes_service.get_gene_position(gene)

            if all(value is not None for value in (chrom, start, end)):
                return (chrom, start, end), 200
            else:
                return {
                    "data": [],
                    "message": "Could not find this gene within our data",
                }, 404

        except GenesServiceNotAvailable as e:
            return {"message": str(e)}, 404
        except Exception as e:
            return {"message": "Internal server error."}, 500
