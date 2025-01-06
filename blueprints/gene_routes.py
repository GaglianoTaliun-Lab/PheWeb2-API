from flask import Blueprint, g
from models import create_genes
from flask_restx import Namespace, Resource

bp = Blueprint("gene_routes", __name__)
api = Namespace("gene", description="Routes related to genes")


@api.route("/<gene>")
class SignificantAssociationTable(Resource):
    def get(self, gene):
        """
        Get association information for a specific gene.
        """
        if "genes" not in g:
            g.genes = create_genes()

        table_data = g.genes.get_genes_table(gene)

        if table_data:
            return table_data, 200
        else:
            return {"data": [], "message": "No data found for this gene"}, 404


@api.route("/gene_position/<gene>")  # TODO: remove this
@api.route("/<gene>/gene_position")
class GenePosition(Resource):
    def get(self, gene):
        """
        Get base-pair and chromosome position of a given gene
        """
        if "genes" not in g:
            g.genes = create_genes()

        chrom, start, end = g.genes.get_gene_position(gene)

        if all(value is not None for value in (chrom, start, end)):
            return (chrom, start, end), 200
        else:
            return {
                "data": [],
                "message": "Could not find this gene without our data",
            }, 404
