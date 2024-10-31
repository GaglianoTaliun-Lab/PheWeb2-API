from flask import Blueprint, jsonify, g, request
from models import create_genes


bp = Blueprint('gene_routes', __name__)

@bp.route('/gene/<gene>', methods=['GET'])
def significant_association_table(gene):
    
    if 'genes' not in g:
        g.genes = create_genes()
        
    table_data = g.genes.get_genes_table(gene)
    if table_data:
        return jsonify(table_data), 200
    else:
        return jsonify({'message': 'No data found for this gene'}), 404