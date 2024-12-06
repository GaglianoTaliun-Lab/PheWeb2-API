import os
from flask import current_app
import gzip
import csv
from typing import Dict
import pysam


class PhewasMatrixReader:
    def __init__(self, variant_code, stratification):
        parts = variant_code.split("-")
        if len(parts) != 4:
            raise ValueError("variant_code should be 'chr-pos-ref-alt'")
        self.data = {
            "chrom": parts[0],
            "pos": int(parts[1]),
            "ref": parts[2],
            "alt": parts[3],
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
                        pheno_data = {"phenocode": phenocode}
                        for field, idx in fields.items():
                            try:
                                pheno_data[field] = float(row_data[idx])
                            except ValueError:
                                pheno_data[field] = row_data[idx]
                        self.data["phenos"].append(pheno_data)
                    return self.data

        return None
