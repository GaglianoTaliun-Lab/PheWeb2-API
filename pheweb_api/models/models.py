from .locus_zoom_utils import get_pheno_region
# from flask import current_app, send_from_directory, send_file
from flask import send_from_directory
from .gene_utils import get_gene_tuples
from .download_utils import getDownloadFunction

import sqlite3
import os
import json
from .variant import PhewasMatrixReader
from .gwas_missing import SNPFetcher
import gzip
from ..conf import get_pheweb_data_dir

"""
My eventual aspiration is to have an SQLite3 database for all these 
data, which will use classes such as these for insertion, get, etc..

For now, while the classes aren't necessary, it creates a decent organizational
structure that we can follow

In addition, these classes allow pre-loading of most data, thereby only having latency
for the query part (again, in theory)
"""


class Tophits:
    def __init__(self, data):
        self.data = data

    def get_tophits(self):
        return self.data


class Genes:
    def __init__(self, data=None, **kwargs: dict):
        self.data = data
        self.gene_region_mapping = kwargs["gene_region_mapping"]

    def connect_to_sqlite(self):
        # connect to sqlite3 database of best-phenos-by-gene
        connection = sqlite3.connect(
            os.path.join(
                get_pheweb_data_dir(), "best-phenos-by-gene.sqlite3"
            )
        )
        connection.row_factory = sqlite3.Row  # each row as dictionary
        return connection

    def get_genes_table(self, gene):
        # get best phenos for the selected gene
        connection = self.connect_to_sqlite()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM best_phenos_for_each_gene WHERE gene='{gene}'")
        results = cursor.fetchone()
        connection.close()

        if results:
            data = json.loads(results["json"])
            response = {
                "gene": gene,
                "data": data,
            }
            return response
        else:
            pass

    def get_gene_position(self, gene):
        chrom, start, end = self.gene_region_mapping[gene]

        return chrom, start, end

    def get_gene_names(self):
        connection = self.connect_to_sqlite()
        cursor = connection.cursor()
        cursor.execute("SELECT gene FROM best_phenos_for_each_gene")
        results = cursor.fetchall()
        connection.close()

        gene_names = [row["gene"] for row in results]
        return gene_names
    
    def get_all_genes(self):
        # Fetch all gene names from the sqlite3 database
        connection = self.connect_to_sqlite()
        cursor = connection.cursor()
        cursor.execute("SELECT gene FROM best_phenos_for_each_gene")
        results = cursor.fetchall()
        connection.close()

        # Return a list of gene names
        gene_dict = {}
        if results:
            for row in results:
                gene_dict[row["gene"]] = {
                    "chrom": self.gene_region_mapping[row["gene"]][0],
                    "start": self.gene_region_mapping[row["gene"]][1],
                    "stop": self.gene_region_mapping[row["gene"]][2],
                }
            return gene_dict
        else:
            pass


class Pheno:
    # TODO: in the future, it would be a thousand times better
    # to have a sqlite3 nosql database with all the manhattan jsons inside,
    # so we could query the database instead of reading the json every single time
    # but for now, send_from_directory is likely the fastest way

    def __init__(self, phenotypes_list=None, interaction_list=None, **kwargs):
        self.pheno = {}
        self.phenotypes_list = phenotypes_list
        self.interaction_list = interaction_list
    
    def get_all_pheno_names(self):
        pheno_dict = {}
        for pheno in self.phenotypes_list:
            pheno_dict[pheno["phenocode"]] = {
                "phenostring": pheno["phenostring"],
                "feature": "pheno"
            }
        return pheno_dict

    def get_phenotypes_list(self, phenocode=None):
        if not phenocode:
            return self.phenotypes_list

        # we can turn self.phenotypes_list into a dict with keys somehow being stratifications to optimize O(n) -> O(1)
        specified_phenos = [
            pheno_info
            for pheno_info in self.phenotypes_list
            if pheno_info["phenocode"] == phenocode
        ]
        return specified_phenos

    def get_interaction_list(self, phenocode):
        if not phenocode:
            return self.interaction_list

        specified_phenos = [
            interaction_info
            for interaction_info in self.interaction_list
            if interaction_info["phenocode"] == phenocode
        ]
        return specified_phenos

    def get_pheno(self, phenocode, stratification):
        if stratification:
            phenocode += stratification

        response = send_from_directory(
            os.path.join(get_pheweb_data_dir(), "manhattan"), f"{phenocode}.json"
        )
        return response

    def get_qq(self, phenocode, stratification):
        if stratification:
            phenocode += stratification

        response = send_from_directory(
            os.path.join(get_pheweb_data_dir(), "qq"), f"{phenocode}.json"
        )
        return response

    def get_sumstats(self, phenocode, filtering_options, suffix=None):
        
        download_function = getDownloadFunction(phenocode, filtering_options, suffix)
        
        return download_function

    def get_region(self, phenocode, stratification, region):
        if stratification:
            phenocode += stratification

        chrom, part2_and_part3 = region.split(":")
        pos_start, pos_end = part2_and_part3.split("-")
        pos_start = int(pos_start)
        pos_end = int(pos_end)

        return get_pheno_region(phenocode, chrom, pos_start, pos_end)

    def get_gwas_missing(self, gwas_missing_data):
        #print(f"{gwas_missing_data=}")
        #print(f"{'6-162025704-T-G' in gwas_missing_data['GS_EXAM_MAX_COM.all.male']}")
        fetcher = SNPFetcher(os.path.join(get_pheweb_data_dir(), "pheno_gz"))
        response = fetcher.process_keys(gwas_missing_data)
        
        #print(f"{response=}")

        return response


class Variant:
    def __init__(self, stratifications: list = None, categories: list = None, all_phenos : list = None, stratification_categories : list = None):
        self.variants = {}
        self.stratifications = stratifications
        self.stratification_categories = stratification_categories
        self.categories = categories
        self.all_phenos = all_phenos

    def get_stratifications(self):
        return self.stratifications
    
    def get_categories(self):
        return self.categories

    def get_variant(self, variant_code, stratification):
        reader = PhewasMatrixReader(variant_code, stratification, self.all_phenos, self.stratification_categories)
        reader.read_matrix()
        response = reader.find_matching_row()
        # print("DEBUG: response", response)
        return response
    
    def get_nearest_genes(self, variant_code):
        try:
            db_path = os.path.join(get_pheweb_data_dir(), "sites", "variants.db")
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT nearest_genes FROM variants WHERE variant_id = ?", (variant_code,))
            nearest_genes = cur.fetchone()[0].split(",")
            print("DEBUG: nearest_genes", nearest_genes)
            print("DEBUG: type of nearest_genes", type(nearest_genes))
            conn.close()
            return {"nearest_genes": nearest_genes} if nearest_genes else None
        except Exception as e:
            print("DEBUG: error", e)
            return {}
    
    def get_variant_rsid(self, variant_code):
        try:
            db_path = os.path.join(get_pheweb_data_dir(), "sites", "autocomplete.db")
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT rsid FROM variants WHERE variant_id = ?", (variant_code,))
            rsid = cur.fetchone()
            print("DEBUG: rsid", rsid)
            print("DEBUG: type of rsid", type(rsid))
            conn.close()
            return {"rsid": rsid} if rsid else None
        except Exception as e:
            print("DEBUG: error", e)
            return {}



def create_genes() -> Genes:
    gene_region_mapping = {
        genename: (chrom, pos1, pos2)
        for chrom, pos1, pos2, genename in get_gene_tuples()
    }

    return Genes(gene_region_mapping=gene_region_mapping)


def create_tophits() -> Tophits:
    with open(
        os.path.join(get_pheweb_data_dir(), "top_hits_1k.json"), "r"
    ) as f:
        data = json.load(f)

    return Tophits(data)


def create_phenotypes_list() -> Pheno:
    try:
        with open(
            os.path.join(get_pheweb_data_dir(), "phenotypes.json")
        ) as f:
            data = json.load(f)

        # split interaction and regular pheno
        phenotypes_list = []
        interaction_list = []

        for pheno in data:
            if "interaction" not in pheno or not pheno["interaction"]:
                phenotypes_list.append(pheno)
            else:
                interaction_list.append(pheno)

    except Exception as e:
        # TODO: logger instead of print?
        print(e)
        return None

    return Pheno(phenotypes_list=phenotypes_list, interaction_list=interaction_list)


def create_variant() -> Variant:
    try:
        with open(
            os.path.join(get_pheweb_data_dir(), "phenotypes.json")
        ) as f:
            data = json.load(f)

    except Exception as e:
        # TODO: logger instead of print?
        print(e)
        return None
    
    stratifications = set()
    stratification_categories = set()
    categories = set()
    all_phenos = []
    
    for pheno in data:
        if "stratification" in pheno:
            stratification_categories = list(pheno["stratification"].keys())
            stratifications.add(".".join(pheno["stratification"].values()))
        if "category" in pheno:
            categories.add(pheno['category'])
        pheno_subset = {
            'phenocode' : pheno['phenocode'],
            'category' : pheno['category'],
            'phenostring' : pheno['phenostring']
            }
        
        if pheno_subset not in all_phenos:
            all_phenos.append(pheno_subset)        
            
    stratifications, categories, all_phenos = list(stratifications), list(categories), list(all_phenos)

    return Variant(stratifications, categories, all_phenos, stratification_categories)
