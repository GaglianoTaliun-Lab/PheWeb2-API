from flask import Blueprint, jsonify, g, request
from models import create_genes
from flask_restx import Namespace, Resource, reqparse

bp = Blueprint('gene_routes', __name__)
api = Namespace('genes', description="Routes related to genes")

@api.route('/gene/<gene>')
class SignificantAssociationTable(Resource):
    def get(gene):
        """
        Get association information for a specific gene.
        """
        if 'genes' not in g:
            g.genes = create_genes()
            
        table_data = g.genes.get_genes_table(gene)
        if table_data:
            return jsonify(table_data), 200
        else:
            return jsonify({'data': [], 'message': 'No data found for this gene'}), 404
    
@api.route('/gene/gene_position/<gene>')
class GenePosition(Resource):
    def get(gene):
        """
        Get base-pair and chromosome position of a given gene
        """
        if 'genes' not in g:
            g.genes = create_genes()
            
        chrom, start, end = g.genes.get_gene_position(gene)
        
        if all(value is not None for value in (chrom, start, end)):
            return jsonify((chrom, start, end)), 200
        else:
            return jsonify({'data': [], 'message': 'Could not find this gene without our data'}), 404 