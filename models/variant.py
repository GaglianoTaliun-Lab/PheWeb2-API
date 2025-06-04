import os
from flask import current_app
import gzip
import csv
from typing import Dict
import pysam
import json


class PhewasMatrixReader:
    def __init__(self, variant_code, stratification, all_phenos : dict):
        parts = variant_code.split("-")
        if len(parts) != 4:
            raise ValueError("variant_code should be 'chr-pos-ref-alt'")
        self.data = {
            "chrom": parts[0],
            "pos": int(parts[1]),
            "ref": parts[2],
            "alt": parts[3],
            "rsids" : [],
            "phenos": [],
        }
        tsvpath = f"matrix.{stratification}.tsv.gz"
        self.filepath = os.path.join(current_app.config["PHEWAS_MATRIX_DIR"], tsvpath)
        csv.register_dialect(
            "pheweb-internal-dialect",
            delimiter="\t",
            quoting=csv.QUOTE_MINIMAL,
            skipinitialspace=True,
        )
        self.phenotype_data_with_index = {}
        self.get_phenotypes_data()
        self.all_phenos = all_phenos

    def get_phenotypes_data(self):
        try:
            phenotypes_file = os.path.join(
                current_app.config["PHENOTYPES_DIR"], "phenotypes.json"
            )
            with open(phenotypes_file) as f:
                data = json.load(f)

            self.phenotype_data_with_index = self.build_phenotypes_index(data)

        except Exception as e:
            print(e)
            self.phenotype_data_with_index = None
            return None

    def build_phenotypes_index(self, phenotypes_data):
        index = {}
        for phenotype in phenotypes_data:
            key = (
                phenotype["phenocode"],
                phenotype["stratification"]["ancestry"],
                phenotype["stratification"]["sex"],
            )
            if key not in index:
                index[key] = []
            index[key].append(phenotype)
        return index

    def read_matrix(self):
        with gzip.open(self.filepath, "rt") as f:
            reader = csv.reader(f, dialect="pheweb-internal-dialect")
            colnames = next(reader)

        assert colnames[0].startswith("#"), colnames
        colnames[0] = colnames[0][1:]

        # self._colidxs: Dict[str, int] = {}  # maps field -> column_index
        # self._colidxs_for_pheno: Dict[str, Dict[str, int]] = {}  # maps phenocode -> field -> column_index
        self._colidxs: Dict[str, int] = {
            colname: idx for idx, colname in enumerate(colnames)
        }  # maps field -> column_index including phenocode

        self.phenotype_fields = {}
        for colname in colnames:
            if "@" in colname:
                field, phenocode = colname.split("@")  # stats_field@phenocode
                if phenocode not in self.phenotype_fields:
                    self.phenotype_fields[phenocode] = {}
                self.phenotype_fields[phenocode][field] = self._colidxs[
                    colname
                ]  # get index of each field of each phenocode

    # def get_phenocodes(self):
    #     return list(self._colidxs_for_pheno)

    def find_matching_row(self):
        with pysam.TabixFile(self.filepath) as tbx:
            for row in tbx.fetch(
                self.data["chrom"], self.data["pos"] - 1, self.data["pos"]
            ):
                row_data = row.split("\t")

                chrom = row_data[self._colidxs["chrom"]]
                pos = int(row_data[self._colidxs["pos"]])
                ref = row_data[self._colidxs["ref"]]
                alt = row_data[self._colidxs["alt"]]
                
                self.data['rsids'] = row_data[self._colidxs["rsids"]]

                if (
                    chrom == self.data["chrom"]
                    and pos == self.data["pos"]
                    and ref == self.data["ref"]
                    and alt == self.data["alt"]
                ):
                    self.data["nearest_genes"] = row_data[
                        self._colidxs.get("nearest_genes")
                    ]  # get nearest gene
                    for phenocode, fields in self.phenotype_fields.items():
                        phenocode_parts = phenocode.split(".")
                        # pheno_basic_info = self.phenotype_data_with_index.get((phenocode_parts[0],phenocode_parts[1],phenocode_parts[2]), [])[0]
                        key = (
                            phenocode_parts[0],
                            phenocode_parts[1],
                            phenocode_parts[2],
                        )
                        
                        pheno_list = self.phenotype_data_with_index.get(key, [])
                        #print(pheno_list)
                        if pheno_list:
                            pheno_basic_info = pheno_list[0]
                        else:
                            pheno_basic_info = None
                            
                        #print(pheno_basic_info)
                        pheno_data = { #TODO : make this flexible for other stratification options?
                            "phenocode": phenocode_parts[0],
                            "stratification": {
                                "ancestry": phenocode_parts[1]
                                if len(phenocode_parts) > 1
                                else None,
                                "sex": phenocode_parts[2]
                                if len(phenocode_parts) > 2
                                else None,
                            },
                            "category": pheno_basic_info["category"]
                            if pheno_basic_info is not None
                            else None,
                            "phenostring": pheno_basic_info["phenostring"]
                            if pheno_basic_info is not None
                            else None,
                            "num_samples": pheno_basic_info["num_samples"]
                            if pheno_basic_info is not None
                            else None,
                            "num_controls": pheno_basic_info["num_controls"]
                            if pheno_basic_info is not None
                            else None,
                            "num_cases": pheno_basic_info["num_cases"]
                            if pheno_basic_info is not None
                            else None,
                        }
                        subset_pheno = {'phenocode':pheno_data['phenocode'],
                                        'category' : pheno_data['category'], 
                                        'phenostring':pheno_data['phenostring']}
                        
                        if subset_pheno in self.all_phenos:
                            self.all_phenos.remove(subset_pheno)
                        for field, idx in fields.items():
                            try:
                                pheno_data[field] = float(row_data[idx])
                            except ValueError:
                                if field == "pval": 
                                    #pass
                                    pheno_data[field] = -1
                                else:
                                    pheno_data[field] = row_data[idx]

                        self.data["phenos"].append(pheno_data)

                    #print(self.all_phenos)
                    for unseen_pheno in self.all_phenos:
                        self.data['phenos'].append({
                            "phenocode": unseen_pheno['phenocode'],
                            "stratification": self.data['phenos'][0]['stratification'],
                            "category": unseen_pheno['category'],
                            "phenostring": unseen_pheno['phenostring'],
                            "num_samples": 0,
                            "num_controls": '',
                            "num_cases": '',
                            "test" : '',
                            "pval" : -1,
                            "beta" : '',
                            "sebeta" : '',
                            "af" : None,
                        })
                    return self.data

        return None
