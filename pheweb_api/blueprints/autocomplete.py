from flask import Blueprint, request, current_app
from flask_restx import Namespace, Resource
import re
from ..models.autocomplete_util import AutocompleteLoading

autocomplete_service = AutocompleteLoading()

bp = Blueprint("autocomplete", __name__)
api = Namespace("autocomplete", description="Routes related to autocomplete")

def search_gene_names(query):
    
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


def search_variant_names(query, chrom=None, pos=None):
    print("DEBUG: search_variant_names called")
    print(f"DEBUG: query: {query}")
    # autocomplete_service = current_app.config["AUTOCOMPLETE"]
    if chrom and pos:
        results = autocomplete_service.query_variants(query, chrom=chrom, pos=pos)
        print(f"DEBUG: variant query results: {results}")
    else:
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

def extract_partial_variant_id(query):
    query = query.strip().upper()
    
    full_pattern = re.compile(
        r"^(CHR)?(?P<chrom>\d+|X|Y|MT)[:\-](?P<pos>\d+)[:\-](?P<ref>[ACGT]+)[:\-](?P<alt>[ACGT]+)$"
    )
    ref_pattern = re.compile(
        r"^(CHR)?(?P<chrom>\d+|X|Y|MT)[:\-](?P<pos>\d+)[:\-](?P<ref>[ACGT]+)$"
    )
    pos_pattern = re.compile(
        r"^(CHR)?(?P<chrom>\d+|X|Y|MT)[:\-](?P<pos>\d+)$"
    )

    for pattern in [full_pattern, ref_pattern, pos_pattern]:
        match = pattern.match(query)
        if match:
            chrom = match.group("chrom").lstrip("CHR")
            pos = match.group("pos")
            ref = match.groupdict().get("ref")
            alt = match.groupdict().get("alt")
            
            variant_parts = [chrom, pos]
            if ref:
                variant_parts.append(ref)
            if alt:
                variant_parts.append(alt)
            return ['-'.join(variant_parts), chrom, pos]

    return None

    

def aggregate(raw_query):
    query = raw_query.lstrip()
    if "-" in query or ":" in query:
        print("DEBUG: query contains - or :")
        partial_variant_id_list = extract_partial_variant_id(query)
        print(f"DEBUG: partial_variant_id_list: {partial_variant_id_list}")
        if partial_variant_id_list:
            return {"suggestions": search_variant_names(partial_variant_id_list[0], chrom=partial_variant_id_list[1], pos=int(partial_variant_id_list[2]))}
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