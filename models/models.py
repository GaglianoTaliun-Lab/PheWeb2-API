from models.locus_zoom_utils import get_pheno_region
from flask import current_app, send_from_directory, send_file
from models.gene_utils import get_gene_tuples

import sqlite3
import os
import json
from .variant import PhewasMatrixReader
from .gwas_missing import SNPFetcher

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
                current_app.config["PHENOTYPES_DIR"], "best-phenos-by-gene.sqlite3"
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


class Pheno:
    # TODO: in the future, it would be a thousand times better
    # to have a sqlite3 nosql database with all the manhattan jsons inside,
    # so we could query the database instead of reading the json every single time
    # but for now, send_from_directory is likely the fastest way

    def __init__(self, phenotypes_list=None, interaction_list=None, **kwargs):
        self.pheno = {}
        self.phenotypes_list = phenotypes_list
        self.interaction_list = interaction_list

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
            current_app.config["MANHATTAN_DIR"], f"{phenocode}.json"
        )
        return response

    def get_qq(self, phenocode, stratification):
        if stratification:
            phenocode += stratification

        response = send_from_directory(
            current_app.config["QQ_DIR"], f"{phenocode}.json"
        )
        return response

    def get_sumstats(self, phenocode, suffix=None):
        if not suffix:
            return send_file(
                current_app.config["PHENO_GZ_DIR"] + f"/{phenocode}.gz",
                as_attachment=True,
                download_name=f"{phenocode}.tsv.gz",
            )

        if "inter-" in suffix:
            return send_file(
                current_app.config["INTERACTION_DIR"] + f"/{phenocode}{suffix}.gz",
                as_attachment=True,
                download_name=f"{phenocode}{suffix}.tsv.gz",
            )

        return send_file(
            current_app.config["PHENO_GZ_DIR"] + f"/{phenocode}{suffix}.gz",
            as_attachment=True,
            download_name=f"{phenocode}{suffix}.tsv.gz",
        )

    def get_region(self, phenocode, stratification, region):
        if stratification:
            phenocode += stratification

        chrom, part2_and_part3 = region.split(":")
        pos_start, pos_end = part2_and_part3.split("-")
        pos_start = int(pos_start)
        pos_end = int(pos_end)

        return get_pheno_region(phenocode, chrom, pos_start, pos_end)

    def get_gwas_missing(self, gwas_missing_data):
        # TODO: process data using SNPFetcher
        print("get_gwas_missing triggered")
        fetcher = SNPFetcher(current_app.config["PHENO_GZ_DIR"])
        response = fetcher.process_keys(gwas_missing_data)

        return response


class Variant:
    def __init__(self, data: list = None):
        self.variants = {}
        self.stratifications = data

    def get_stratifications(self):
        return self.stratifications

    def get_variant(self, variant_code, stratification):
        reader = PhewasMatrixReader(variant_code, stratification)
        reader.read_matrix()
        response = reader.find_matching_row()
        return response


# functions to create class (factory pattern)
# def create_phenotypes() -> Phenotypes:

#     with open(os.path.join(current_app.config['PHENOTYPES_DIR'], 'phenotypes.json'), 'r') as f:
#             data = json.load(f)

#     return Phenotypes(data)


def create_genes() -> Genes:
    gene_region_mapping = {
        genename: (chrom, pos1, pos2)
        for chrom, pos1, pos2, genename in get_gene_tuples()
    }

    return Genes(gene_region_mapping=gene_region_mapping)


def create_tophits() -> Tophits:
    with open(
        os.path.join(current_app.config["PHENOTYPES_DIR"], "top_hits_1k.json"), "r"
    ) as f:
        data = json.load(f)

    return Tophits(data)


def create_phenotypes_list() -> Pheno:
    try:
        with open(
            os.path.join(current_app.config["PHENOTYPES_DIR"], "phenotypes.json")
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
            os.path.join(current_app.config["PHENOTYPES_DIR"], "phenotypes.json")
        ) as f:
            data = json.load(f)

    except Exception as e:
        # TODO: logger instead of print?
        print(e)
        return None

    stratifications: list = list(
        set(
            [
                ".".join(pheno["stratification"].values())
                for pheno in data
                if "stratification" in pheno
            ]
        )
    )
    return Variant(stratifications)
