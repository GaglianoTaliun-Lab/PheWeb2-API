from flask import Blueprint, jsonify, g, request, current_app
from models import create_phenotypes_list, create_genes, create_variant
from models.utils import extract_variants
from flask_restx import Namespace, Resource, reqparse
import re


bp = Blueprint("autocomplete", __name__)
api = Namespace("autocomplete", description="Routes related to autocomplete")


class PhenotypeServiceNotAvailable(Exception):
    pass
class GenesServiceNotAvailable(Exception):
    pass
class VariantServiceNotAvailable(Exception):
    pass

def get_genes_service():
    if "genes" not in g:
        g.genes = create_genes()
        if g.genes is None:
            raise GenesServiceNotAvailable(
                "Could not create gene service. Check if data path (named generated-by-pheweb/ by default) is correctly configured in .env or config.py."
            )
    return g.genes

def fuzzy_search_genes(gene_dict, query, max_results=5):
    query = query.upper()
    result = []
    for gene, val in gene_dict.items():
        if query in gene.upper():
            result.append({
                "gene": gene,
                "chrom": val["chrom"],
                "start": val["start"],
                "stop": val["stop"],
                "feature": "gene"
            })
    return result[:max_results]
    

def search_gene_names(query):
    genes_service = get_genes_service()
    gene_dict = genes_service.get_all_genes()
    return fuzzy_search_genes(gene_dict, query)


def get_pheno_service():
    if "pheno" not in g:
        g.pheno = create_phenotypes_list()
        if g.pheno is None:
            raise PhenotypeServiceNotAvailable(
                "Could not create phenotype service. Check if data path (named generated-by-pheweb/ by default) is correctly configured in .env or config.py."
            )
    return g.pheno


def fuzzy_search_pheno(pheno_dict, query, max_results=15):
    query_lower = query.lower()
    result = []

    for phenocode, val in pheno_dict.items():
        phenostring = val["phenostring"]
        if query_lower in phenocode.lower() or query_lower in phenostring.lower():
            result.append({
                "phenocode": phenocode,
                "phenostring": phenostring,
                "feature": "pheno"
            })

    return result[:max_results]


def search_pheno_names(query):
    pheno_service = get_pheno_service()
    pheno_dict = pheno_service.get_all_pheno_names()
    return fuzzy_search_pheno(pheno_dict, query)


def search_variant_names(query):
    print("DEBUG: search_variant_names called")
    variant_service = current_app.config["VARIANTS"]
    results = variant_service.query_variants(query)
    print("DEBUG: results", results)
    output = []
    for rsid, variant_id in results:
        output.append({
            "rsid": rsid,
            "variant_id": variant_id,
            "feature": "variant"
        })
    return output


def extract_standard_variant_id(query):
    query = query.strip().upper()
    pattern = re.compile(
        r"^(CHR)?(?P<chrom>\d+|X|Y|MT)[:\-](?P<pos>\d+)[:\-](?P<ref>[ACGT]+)[:\-](?P<alt>[ACGT]+)$"
    )
    match = pattern.match(query)
    if match:
        chrom = match.group("chrom").lstrip("CHR")  # remove 'CHR' if exists
        pos = match.group("pos")
        ref = match.group("ref")
        alt = match.group("alt")
        return f"{chrom}-{pos}-{ref}-{alt}"
    return None
    

def aggregate(raw_query):
    query = raw_query.lstrip()
    if query.lower().startswith("chr"):
        return {"suggestions": search_variant_names(query.lower()[3:])}
    standard_variant_id = extract_standard_variant_id(query)
    if standard_variant_id:
        return {"suggestions": search_variant_names(standard_variant_id)}
    if query.lower().startswith("rs"):
        return {"suggestions": search_variant_names(query.lower())}
    
    if(query == ""):
        return({"suggestions": []})
    pheno_results = search_pheno_names(query)
    gene_results = search_gene_names(query)
    all_results = [*pheno_results, *gene_results]
    return {"suggestions": all_results}





@api.route("/")
class Autocomplete(Resource):
    def get(self):
        """
        Get autocomplete suggestions for gene and phenotype names
        """
        try:
            query = request.args.get('query', '')
            results = aggregate(query)
            if results:
                return results, 200
            else:
                return {"message": "Could not find any results"}, 404
        except Exception as e:
            return {"message": "Internal server error."}, 500