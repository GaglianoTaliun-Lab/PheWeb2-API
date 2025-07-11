from flask import Blueprint, request, current_app
from flask_restx import Namespace, Resource
import re


bp = Blueprint("autocomplete", __name__)
api = Namespace("autocomplete", description="Routes related to autocomplete")

    
def search_gene_names(query):
    autocomplete_service = current_app.config["AUTOCOMPLETE"]
    results = autocomplete_service.query_genes(query)
    # print(f"DEBUG: results: {results}")
    output = []
    for gene, chrom, start, stop in results:
        output.append({
            "gene": gene,
            "chrom": chrom,
            "start": start,
            "stop": stop,
            "feature": "gene"
        })
    return output


def search_pheno_names(query):
    autocomplete_service = current_app.config["AUTOCOMPLETE"]
    results = autocomplete_service.query_phenotypes(query)
    # print(f"DEBUG: results: {results}")
    output = []
    for phenocode, phenostring in results:
        output.append({
            "phenocode": phenocode,
            "phenostring": phenostring,
            "feature": "pheno"
        })
    return output


def search_variant_names(query):
    print("DEBUG: search_variant_names called")
    print(f"DEBUG: query: {query}")
    autocomplete_service = current_app.config["AUTOCOMPLETE"]
    results = autocomplete_service.query_variants(query)
    # print("DEBUG: results", results)
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
    if "-" in query or ":" in query:
        standard_variant_id = extract_standard_variant_id(query)
        if standard_variant_id:
            return {"suggestions": search_variant_names(standard_variant_id)}
    elif query.lower().startswith("rs"):
        return {"suggestions": search_variant_names(query.lower())}
    
    elif query == "":
        return({"suggestions": []})
    else:
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