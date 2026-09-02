import gzip
from pathlib import Path
import json
import sqlite3
import pysam

from pheweb_api import conf
from pheweb_api.utils import *
from pheweb_api.file_utils import *


from pheweb_api.load.matrix import create_matrix_tbi


def dummy_summary_stats():

    summary_stat = get_generated_path("DUMMY_COM.regenie.gz")

    header = "CHROM GENPOS ID ALLELE0 ALLELE1 A1FREQ INFO N TEST BETA SE CHISQ LOG10P EXTRA\n"
    line1 = "19 44908822 19:44908822:C:T C T 0.0808602 1.00121 26392 ADD-CONDTL -0.273429 0.0155408 309.559 68.5648 NA\n"
    line2 = "19 44908822 19:44908822:C:T C T 0.0808602 1.00121 26392 ADD-INT_SNP 0.0102064 0.051343 0.0395168 0.074467 NA\n"
    line3 = "19 44908822 19:44908822:C:T C T 0.0808602 1.00121 26392 ADD-INT_SNPxsex -0.186739 0.0326695 32.6726 7.96232 NA\n"
    line4 = "19 44908822 19:44908822:C:T C T 0.0808602 1.00121 26392 ADD-INT_2DF NA NA 301.041 65.3703 NA"
    with gzip.open(summary_stat, "wt") as f:
        f.writelines([header, line1, line2, line3, line4])

    return summary_stat


def dummy_manifest_file(summary_stat) -> str:

    manifest = get_generated_path("manifest-example.csv")

    header = "phenocode,phenostring,assoc_files,num_samples,num_cases,num_controls,category,interaction,stratification.sex,stratification.ancestry\n"
    line1 = f"DUMMY_COM,dummy,{summary_stat},26392,,,dummy_category,,both,all\n"
    line2 = f"DUMMY_COM,dummy,{summary_stat},26392,,,dummy_category,sex,both,all\n"

    with open(manifest, "w") as f:
        f.writelines([header, line1, line2])

    return manifest


def dummy_phenolist() -> str:

    phenolist_data = [
        {
            "assoc_files": [
                "/lustre07/scratch/jordboul/PheWeb/Dev/PheWeb2-API/generated-by-pheweb/tmp/generated-by-pheweb/DUMMY_COM.regenie.gz"
            ],
            "category": "dummy_category",
            "interaction": None,
            "num_cases": "",
            "num_controls": "",
            "num_samples": 26392,
            "phenocode": "DUMMY_COM",
            "phenostring": "dummy",
            "stratification": {
                "ancestry": "all",
                "sex": "both"
            }
        },
        {
            "assoc_files": [
                "/lustre07/scratch/jordboul/PheWeb/Dev/PheWeb2-API/generated-by-pheweb/tmp/generated-by-pheweb/DUMMY_COM.regenie.gz"
            ],
            "category": "dummy_category",
            "interaction": "sex",
            "num_cases": "",
            "num_controls": "",
            "num_samples": 26392,
            "phenocode": "DUMMY_COM",
            "phenostring": "dummy",
            "stratification": {
                "ancestry": "all",
                "sex": "both"
            }
        }
    ]

    phenolist_filepath = get_filepath("phenolist", must_exist=False)

    with open(phenolist_filepath, "w") as phenolist_file:
        json.dump(phenolist_data, phenolist_file)

    return phenolist_filepath


def dummy_summary_stats_2():

    summary_stat = get_generated_path("DUMMY_2_COM.regenie.gz")

    header = "CHROM GENPOS ID ALLELE0 ALLELE1 A1FREQ A1FREQ_CASES A1FREQ_CONTROLS INFO N N_CASES N_CONTROLS TEST BETA SE CHISQ LOG10P EXTRA\n"
    line1 = "1 21506237 1:21506237:C:T C T 0.0704679 0.0708858 0.546808 1.00647 25460 22179 3281 ADD-CONDTL 0.51648 0.094504 33.2653 8.09473 NA\n"
    line2 = "1 21506237 1:21506237:C:T C T 0.0704679 0.0708858 0.546808 1.00647 25460 22179 3281 ADD-INT_SNP -0.897824 0.161193 29.8844 7.33858 NA\n"
    line3 = "1 21506237 1:21506237:C:T C T 0.0704679 0.0708858 0.546808 1.00647 25460 22179 3281 ADD-INT_SNPxsex 0.674982 0.10785 39.9898 9.59296 NA\n"
    line4 = "1 21506237 1:21506237:C:T C T 0.0704679 0.0708858 0.546808 1.00647 25460 22179 3281 ADD-INT_2DF NA NA 42.6455 9.26035 NA"
    with gzip.open(summary_stat, "wt") as f:
        f.writelines([header, line1, line2, line3, line4])

    return summary_stat


def dummy_manifest_file_2(summary_stat_2) -> str:

    manifest = get_generated_path("manifest-example-2.csv")

    header = "phenocode,phenostring,assoc_files,num_samples,num_cases,num_controls,category,interaction,stratification.sex,stratification.ancestry\n"
    line1 = f"DUMMY_2_COM,dummy_2,{summary_stat_2},25460,22179,3281,other_category,,both,all\n"
    line2 = f"DUMMY_2_COM,dummy_2,{summary_stat_2},25460,22179,3281,other_category,sex,both,all\n"

    with open(manifest, "w") as f:
        f.writelines([header, line1, line2])

    return manifest


def dummy_gene_aliases() -> str:
    """
    Creating a dummmy gene_aliases containing a single (alias, canonical) gene combinaison.
    """

    # alias, canonicals
    dummy_aliases = {
        "APOE": "APOE",
        "ALPL": "ALPL"
    }

    aliases_filepath = Path(get_filepath(
        "gene-aliases-sqlite3", must_exist=False))
    aliases_tmp_filepath = Path(get_tmp_path(aliases_filepath))
    db = sqlite3.connect(str(aliases_tmp_filepath))
    with db:
        db.execute(
            "CREATE TABLE gene_aliases (alias TEXT PRIMARY KEY, canonicals_comma TEXT)"
        )
        db.executemany(
            "INSERT INTO gene_aliases VALUES (?,?)", sorted(
                dummy_aliases.items())
        )

    aliases_tmp_filepath.replace(aliases_filepath)

    return aliases_filepath


def dummy_genes() -> str:
    genes_filepath = get_filepath("genes", must_exist=False)

    with open(genes_filepath, "w") as genes_file:
        genes_file.write("1\t21509397\t21578410\tALPL\tENSG00000162551\n")
        genes_file.write("19\t44905791\t44909393\tAPOE\tENSG00000130203")

    return genes_filepath


def dummy_rsids() -> str:

    rsids_filepath = get_filepath("rsids", must_exist=False)

    with gzip.open(rsids_filepath, "wt") as rsids_f:
        rsids_f.write("1\t21506237\trs3856178\tC\tT\n")
        rsids_f.write("19\t44908822\trs7412\tC\tT")

    return rsids_filepath


def dummy_unanno() -> str:

    unanno_filepath = get_filepath("unanno", must_exist=False)

    header = "chrom\tpos\tref\talt\n"
    line1 = "19\t44908822\tC\tT\n"
    with gzip.open(unanno_filepath, "wt") as unanno_file:
        unanno_file.writelines([header, line1])

    return unanno_filepath


def dummy_sites_rsid() -> str:

    sites_rsids_filepath = get_filepath("sites-rsids", must_exist=False)

    header = "chrom\tpos\tref\talt\trsids\n"
    line1 = "19\t44908822\tC\tT\trs7412\n"
    with gzip.open(sites_rsids_filepath, "wt") as sites_rsids_file:
        sites_rsids_file.writelines([header, line1])

    return sites_rsids_filepath


def dummy_sites() -> str:

    sites_filepath = get_filepath("sites", must_exist=False)

    header = "chrom\tpos\tref\talt\trsids\tnearest_genes\n"
    line1 = "19\t44908822\tC\tT\trs7412\tAPOE\n"
    with gzip.open(sites_filepath, "wt") as sites_file:
        sites_file.writelines([header, line1])

    return sites_filepath


def dummy_cpras_rsids() -> str:

    cpras_rsids_filepath = get_filepath(
        "cpras-rsids-sqlite3", must_exist=False)

    db_conn = sqlite3.connect(str(cpras_rsids_filepath))
    with db_conn:
        db_conn.execute("CREATE TABLE cpras_rsids (cpra TEXT, rsid TEXT)")
        db_conn.executemany(
            "INSERT INTO cpras_rsids (cpra, rsid) VALUES (?,?)",
            [("19-44908822-C-T", "rs7412")],
        )
        db_conn.execute("CREATE INDEX rsid_idx ON cpras_rsids (rsid)")

    return cpras_rsids_filepath


def dummy_parsed() -> tuple[str, str]:

    header = "chrom\tpos\tref\talt\ttest\tpval\tbeta\tsebeta\taf\timp_quality\tn_samples\n"
    line1 = "19\t44908822\tC\tT\tADD-CONDTL\t2.7e-69\t-0.27\t0.016\t0.081\t1.00121\t26392"

    dummy_phenocode = "DUMMY_COM.all.both"
    dummy_parsed_filepath = get_pheno_filepath(
        "parsed", dummy_phenocode, must_exist=False)

    with open(dummy_parsed_filepath, "wt") as dummy_parsed_file:
        dummy_parsed_file.writelines([header, line1])

    # ==== interaction ====

    header = "chrom\tpos\tref\talt\ttest\tpval\tbeta\tsebeta\taf\timp_quality\tn_samples\n"
    line1 = "19\t44908822\tC\tT\tADD-INT_SNPxsex\t1.1e-08\t-0.19\t0.033\t0.081\t1.00121\t26392"

    dummy_interaction_phenocode = "DUMMY_COM.interaction-sex.all.both"
    dummy_interaction_filepath = get_pheno_filepath(
        "parsed", dummy_interaction_phenocode, must_exist=False)

    with open(dummy_interaction_filepath, "wt") as dummy_interaction_file:
        dummy_interaction_file.writelines([header, line1])

    return dummy_parsed_filepath, dummy_interaction_filepath


def dummy_augment_pheno() -> tuple[str, str]:

    # ==== pheno_gz ====
    header = "chrom\tpos\tref\talt\trsids\tnearest_genes\ttest\tpval\tbeta\tsebeta\taf\timp_quality\tn_samples\n"
    line1 = "19\t44908822\tC\tT\trs7412\tAPOE\tADD-CONDTL\t2.7e-69\t-0.27\t0.016\t0.081\t1.00121\t26392\n"

    dummy_phenocode = "DUMMY_COM.all.both"
    dummy_parsed_filepath = get_pheno_filepath(
        "pheno_gz", dummy_phenocode, must_exist=False)
    dummy_parsed_filepath_tmp = get_tmp_path(dummy_parsed_filepath)

    with open(dummy_parsed_filepath_tmp, "w") as dummy_parsed_file_tmp:
        dummy_parsed_file_tmp.writelines([header, line1])

    convert_VariantFile_to_IndexedVariantFile(
        dummy_parsed_filepath_tmp, dummy_parsed_filepath)

    # ==== interaction ====

    header = "chrom\tpos\tref\talt\trsids\tnearest_genes\ttest\tpval\tbeta\tsebeta\taf\timp_quality\tn_samples\n"
    line1 = "19\t44908822\tC\tT\trs7412\tAPOE\tADD-INT_SNPxsex\t1.1e-08\t-0.19\t0.033\t0.081\t1.00121\t26392\n"

    dummy_interaction_phenocode = "DUMMY_COM.interaction-sex.all.both"
    dummy_interaction_filepath = get_pheno_filepath(
        "interaction", dummy_interaction_phenocode, must_exist=False)

    dummy_interaction_filepath_tmp = get_tmp_path(dummy_interaction_filepath)
    with open(dummy_interaction_filepath_tmp, "w") as dummy_interaction_file_tmp:
        dummy_interaction_file_tmp.writelines([header, line1])

    convert_VariantFile_to_IndexedVariantFile(
        dummy_interaction_filepath_tmp, dummy_interaction_filepath)  # note: aussi fixé le typo _tmp manquant ici

    return dummy_parsed_filepath, dummy_interaction_filepath


def dummy_matrix() -> str:

    header = "#chrom\tpos\tref\talt\trsids\tnearest_genes\ttest@DUMMY_COM.all.both\tpval@DUMMY_COM.all.both\tbeta@DUMMY_COM.all.both\tsebeta@DUMMY_COM.all.both\taf@DUMMY_COM.all.both\timp_quality@DUMMY_COM.all.both\tn_samples@DUMMY_COM.all.both\n"
    line1 = "19\t44908822\tC\tT\trs7412\tAPOE\tADD-CONDTL\t2.7e-69\t-0.27\t0.016\t0.081\t1.00121\t26392"

    stratification_paths = get_stratification_paths(
        get_phenolist_no_interaction())

    matrix_gz_stratified_filepath = get_pheno_filepath(
        "matrix-stratified", stratification_paths[0], must_exist=False
    )

    with pysam.BGZFile(matrix_gz_stratified_filepath, "wb") as f:
        f.write(header.encode())
        f.write(line1.encode())

    create_matrix_tbi(matrix_gz_stratified_filepath)

    assert os.path.exists(matrix_gz_stratified_filepath + ".tbi")

    return matrix_gz_stratified_filepath


def dummy_pvalues_for_each_gene() -> str:

    out_filepath = Path(get_filepath(
        "best-phenos-by-gene-sqlite3", must_exist=False))

    data = ("APOE",
            '[{"test": "ADD-CONDTL", "category": "dummy_category", "interaction": "sex", "num_cases": "", "num_controls": "", "num_samples": 26392, "phenocode": "DUMMY_COM.all.both", "phenostring": "dummy", "stratification": {"ancestry": "all", "sex": "both"}, "pval": 2.7e-69, "beta": -0.27, "sebeta": 0.016, "af": 0.081, "imp_quality": 1.00121, "n_samples": 26392, "distance_to_true_start": 3031, "is_in_real_range": true}]')

    db = sqlite3.connect(str(out_filepath))
    with db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS best_phenos_for_each_gene (gene TEXT PRIMARY KEY, json TEXT)"
        )
        db.executemany(
            "INSERT INTO best_phenos_for_each_gene (gene, json) VALUES (?,?)",
            [data],
        )

    return out_filepath


def dummy_manhattan() -> tuple[str, str]:

    dummy_json = {"variant_bins": [],
                  "unbinned_variants":
                  [{"chrom": "19", "pos": 44908822, "ref": "C",
                    "alt": "T", "rsids": "rs7412", "nearest_genes": "APOE",
                    "test": "ADD-CONDTL", "pval": 2.7e-69, "beta": -0.27,
                    "sebeta": 0.016, "af": 0.081, "imp_quality": 1.00121,
                    "n_samples": 26392, "num_significant_in_peak": 1, "peak": True}]}

    dummy_phenocode = "DUMMY_COM.all.both"
    manhattan_filepath = get_pheno_filepath(
        "manhattan", dummy_phenocode, must_exist=False)

    with open(manhattan_filepath, "w") as manhattan_file:
        json.dump(dummy_json, manhattan_file)

    dummy_interaction_phenocode = "DUMMY_COM.interaction-sex.all.both"
    manhattan_interaction_filepath = get_pheno_filepath(
        "manhattan", dummy_interaction_phenocode, must_exist=False)

    dummy_interaction_json = {"variant_bins": [],
                              "unbinned_variants": [{"chrom": "19", "pos": 44908822, "ref": "C",
                                                     "alt": "T", "rsids": "rs7412", "nearest_genes": "APOE",
                                                     "test": "ADD-INT_SNPxsex", "pval": 1.1e-08, "beta": -0.19,
                                                     "sebeta": 0.033, "af": 0.081, "imp_quality": 1.00121,
                                                     "n_samples": 26392, "num_significant_in_peak": 1, "peak": True}]}

    with open(manhattan_interaction_filepath, "w") as manhattan_interaction_file:
        json.dump(dummy_interaction_json, manhattan_interaction_file)

    return manhattan_filepath, manhattan_interaction_filepath


def dummy_qq():

    dummy_json = {"by_maf": [{"maf_range": [0.08100000023841858, 0.08100000023841858],
                              "count": 0, "qq": {}}, {"maf_range": [0.08100000023841858, 0.08100000023841858],
                                                      "count": 0, "qq": {}}, {"maf_range": [0.08100000023841858, 0.08100000023841858],
                                                                              "count": 0, "qq": {}}, {"maf_range": [0.08100000023841858, 0.08100000023841858],
                                                                                                      "count": 1, "qq": {"bins": [], "max_exp_qval": 0.3010299956639812}}],
                  "overall": {"count": 1, "gc_lambda": {}}, "ci": []}

    dummy_phenocode = "DUMMY_COM.all.both"
    qq_filepath = get_pheno_filepath("qq", dummy_phenocode, must_exist=False)

    with open(qq_filepath, "w") as qq_file:
        json.dump(dummy_json, qq_file)

    dummy_interaction_phenocode = "DUMMY_COM.interaction-sex.all.both"
    qq_interaction_filepath = get_pheno_filepath(
        "qq", dummy_interaction_phenocode, must_exist=False)

    dummy_interaction_json = {"by_maf": [{"maf_range": [0.08100000023841858, 0.08100000023841858],
                                          "count": 0, "qq": {}}, {"maf_range": [0.08100000023841858, 0.08100000023841858],
                                                                  "count": 0, "qq": {}}, {"maf_range": [0.08100000023841858, 0.08100000023841858],
                                                                                          "count": 0, "qq": {}}, {"maf_range": [0.08100000023841858, 0.08100000023841858],
                                                                                                                  "count": 1, "qq": {"bins": [], "max_exp_qval": 0.3010299956639812}}],
                              "overall": {"count": 1, "gc_lambda": {}}, "ci": []}

    with open(qq_interaction_filepath, "w") as qq_interaction_file:
        json.dump(dummy_interaction_json, qq_interaction_file)

    return qq_filepath, qq_interaction_filepath


def dummy_phenotypes() -> tuple[str, str]:
    out_filepath = get_filepath("phenotypes_summary", must_exist=False)
    out_filepath_tsv = get_filepath("phenotypes_summary_tsv", must_exist=False)

    json_phenotypes = [{"phenocode": "DUMMY_COM", "pval": 2.7e-69,
                        "nearest_genes": "APOE", "chrom": "19", "pos": 44908822,
                        "ref": "C", "alt": "T", "rsids": "rs7412", "num_peaks": 1,
                        "stratification": {"ancestry": "all", "sex": "both"},
                        "interaction": None, "num_samples": 26392,
                        "num_controls": "", "num_cases": "", "category": "dummy_category",
                        "phenostring": "dummy"},
                       {"phenocode": "DUMMY_COM", "pval": 1.1e-08, "nearest_genes": "APOE",
                        "chrom": "19", "pos": 44908822, "ref": "C", "alt": "T",
                        "rsids": "rs7412", "num_peaks": 1,
                        "stratification": {"ancestry": "all", "sex": "both"},
                        "interaction": "sex", "num_samples": 26392, "num_controls": "",
                        "num_cases": "", "category": "dummy_category", "phenostring": "dummy"}]

    with open(out_filepath, "w") as out_file:
        json.dump(json_phenotypes, out_file)

    header = "chrom\tpos\tref\talt\trsids\tnearest_genes\tpval\tnum_cases\tnum_controls\tnum_samples\tnum_peaks\tinteraction\tphenostring\tphenocode\tstratification\tcategory\n"
    line1 = "19\t44908822\tC\tT\trs7412\tAPOE\t2.7e-69\t26392\t1\tdummy\tDUMMY_COM\t{'ancestry': 'all', 'sex': 'both'}\tdummy_category\n"
    line2 = "19\t44908822\tC\tT\trs7412\tAPOE\t1.1e-08\t26392\t1\tsex\tdummy\tDUMMY_COM\t{'ancestry': 'all', 'sex': 'both'}\tdummy_category"

    with open(out_filepath_tsv, "w") as out_tsv_file:
        out_tsv_file.writelines([header, line1, line2])

    return out_filepath, out_filepath_tsv


def dummy_top_hits() -> tuple[str, str, str]:

    out_filepath_json = get_filepath("top-hits", must_exist=False)
    out_filepath_1k_json = get_filepath("top-hits-1k", must_exist=False)
    out_filepath_tsv = get_filepath("top-hits-tsv", must_exist=False)

    data = [{"af": 0.081, "alt": "T", "beta": -0.27, "category": "dummy_category",
             "chrom": "19", "imp_quality": 1.00121, "interaction": None,
             "n_samples": 26392, "nearest_genes": "APOE", "num_significant_in_peak": 1,
             "peak": True, "phenocode": "DUMMY_COM", "phenostring": "dummy", "pos": 44908822,
             "pval": 2.7e-69, "ref": "C", "rsids": "rs7412", "sebeta": 0.016,
             "stratification": {"ancestry": "all", "sex": "both"},
             "test": "ADD-CONDTL"},
            {"af": 0.081, "alt": "T", "beta": -0.19, "category": "dummy_category",
            "chrom": "19", "imp_quality": 1.00121, "interaction": "sex", "n_samples": 26392,
             "nearest_genes": "APOE", "num_significant_in_peak": 1, "peak": True,
             "phenocode": "DUMMY_COM", "phenostring": "dummy", "pos": 44908822, "pval": 1.1e-08,
             "ref": "C", "rsids": "rs7412", "sebeta": 0.033, "stratification": {"ancestry": "all", "sex": "both"}, "test": "ADD-INT_SNPxsex"}]

    with open(out_filepath_json, "w") as out_file_json:
        json.dump(data, out_file_json)

    with open(out_filepath_1k_json, "w") as out_file_json:
        json.dump(data, out_file_json)

    header = "chrom\tpos\tref\talt\trsids\tnearest_genes\ttest\tpval\tbeta\tsebeta\taf\timp_quality\tn_samples\tstratification\tphenocode\tpeak\tinteraction\tcategory\tphenostring\tnum_significant_in_peak\n"
    line1 = "19\t44908822\tC\tT\trs7412\tAPOE\tADD-CONDTL\t2.7e-69\t-0.27\t0.016\t0.081\t1.00121\t{'ancestry': 'all', 'sex': 'both'}\tDUMMY_COM\tTrue\tdummy_category\tdummy\t1\n"
    line2 = "19\t44908822\tC\tT\trs7412\tAPOE\tADD-INT_SNPxsex\t1.1e-08\t-0.19\t0.033\t0.081\t1.00121\t26392\t{'ancestry': 'all', 'sex': 'both'}\tDUMMY_COM\tTrue\tsex\tdummy_category\tdummy\t1"

    with open(out_filepath_tsv, "w") as tsv_file:
        tsv_file.writelines([header, line1, line2])

    return out_filepath_json, out_filepath_1k_json, out_filepath_tsv


def dummy_best_of_pheno():

    dummy_phenocode = "DUMMY_COM.all.both"
    dummy_interaction_phenocode = "DUMMY_COM.interaction-sex.all.both"

    best_of_pheno_filepath = get_pheno_filepath(
        "best_of_pheno", dummy_phenocode, must_exist=False)

    header = "chrom\tpos\tref\talt\trsids\tnearest_genes\ttest\tpval\tbeta\tsebeta\taf\timp_quality\tn_samples\n"
    line1 = "19\t44908822\tC\tT\trs7412\tAPOE\tADD-CONDTL\t2.7e-69\t-0.27\t0.016\t0.081\t1.00121\t26392"

    with gzip.open(best_of_pheno_filepath, "wt") as best_of_pheno_file:
        best_of_pheno_file.writelines([header, line1])

    best_of_pheno_interaction_filepath = get_pheno_filepath(
        "best_of_pheno", dummy_interaction_phenocode, must_exist=False)

    line1 = "19\t44908822\tC\tT\trs7412\tAPOE\tADD-INT_SNPxsex\t1.1e-08\t-0.19\t0.033\t0.081\t1.00121\t26392"

    with gzip.open(best_of_pheno_interaction_filepath, "wt") as best_of_pheno_interaction_file:
        best_of_pheno_interaction_file.writelines([header, line1])

    return best_of_pheno_filepath, best_of_pheno_interaction_filepath


def dummmy_variants_db() -> str:

    db_path = get_filepath("variants_db", must_exist=False)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
                        CREATE TABLE IF NOT EXISTS variants (
                            id INTEGER PRIMARY KEY,
                            rsid TEXT,
                            variant_id TEXT,
                            nearest_genes TEXT
                        )
                    """)

    rows = [(1, "rs7412", "19-44908822-C-T", "APOE")]

    cur.execute("BEGIN TRANSACTION")
    cur.executemany(
        "INSERT INTO variants (id, rsid, variant_id, nearest_genes) VALUES (?, ?, ?, ?)", rows
    )
    conn.commit()

    return db_path


def dummy_autocomplete_db() -> str:

    db_path = get_filepath("autocomplete_db", must_exist=False)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # ==== variants ====
    cur.execute("""
                    CREATE TABLE IF NOT EXISTS variants (
                        id INTEGER PRIMARY KEY,
                        rsid TEXT,
                        variant_id TEXT,
                        chrom TEXT,
                        pos INTEGER
                    )
                """)

    rows = [(1, "rs7412", "19-44908822-C-T", "19", 44908822)]

    cur.execute("BEGIN TRANSACTION")
    cur.executemany(
        "INSERT INTO variants (id, rsid, variant_id, chrom, pos) VALUES (?, ?, ?, ?, ?)", rows
    )
    conn.commit()

    # ==== genes ====
    cur.execute("""
                    CREATE TABLE IF NOT EXISTS genes (
                        gene_id TEXT PRIMARY KEY,
                        chrom TEXT,
                        start INTEGER,
                        stop INTEGER
                    )
                """)

    rows = [("APOE", "19", 44905791, 44909393)]

    cur.execute("BEGIN TRANSACTION")
    cur.executemany(
        "INSERT INTO genes (gene_id, chrom, start, stop) VALUES (?, ?, ?, ?)", rows)
    conn.commit()

    cur.execute("""
        CREATE TABLE phenotypes (
            phenocode TEXT PRIMARY KEY,
            phenostring TEXT
        )
    """)

    rows = [
        ("DUMMY_COM", "dummy")
    ]
    cur.execute("BEGIN TRANSACTION")
    cur.executemany(
        "INSERT INTO phenotypes (phenocode, phenostring) VALUES (?, ?)", rows)
    conn.commit()

    cur.execute("""
    CREATE VIRTUAL TABLE phenotypes_fts USING fts5(
        phenocode,
        phenostring,
        content=phenotypes,
        content_rowid=rowid
        )
    """)
    cur.execute(
        "INSERT INTO phenotypes_fts(phenotypes_fts) VALUES ('rebuild')")
    conn.commit()

    return db_path


def simulate_first_time_ingest():

    summary_stat_filepath = dummy_summary_stats()
    dummy_manifest_file(summary_stat_filepath)
    dummy_phenolist()
    dummy_gene_aliases()
    dummy_genes()
    dummy_rsids()

    dummy_unanno()
    dummy_sites_rsid()
    dummy_sites()
    dummmy_variants_db()

    dummy_cpras_rsids()

    dummy_parsed()
    dummy_augment_pheno()

    dummy_matrix()

    dummy_pvalues_for_each_gene()
    dummy_manhattan()
    dummy_qq()
    dummy_phenotypes()
    dummy_top_hits()
    dummy_best_of_pheno()

    dummy_autocomplete_db()
