import os.path

# Please create your own configuration file and do not overwrite this file

BASE_DIR = os.path.join(os.sep, "PATH", "TO", "YOUR", "DATA", "DIR")

PHENOTYPES_DIR = os.path.join(BASE_DIR)
MANHATTAN_DIR = os.path.join(BASE_DIR, "manhattan")
QQ_DIR = os.path.join(BASE_DIR, "qq")
PHENO_GZ_DIR = os.path.join(BASE_DIR, "pheno_gz")
BEST_OF_PHENO_DIR = os.path.join(BASE_DIR, "best_of_pheno")

CORS_ORIGINS = ["http://PATH/TO/YOUR/UI"]

hg_build_number = 38

stratified = True

pval_is_neglog10 = True

show_manhattan_filter_button = True

# This is an example for regenie's output columns
field_aliases = {
    "CHROM": "chrom",
    "GENPOS": "pos",
    "ALLELE0": "ref",
    "ALLELE1": "alt",
    "A1FREQ": "af",
    "BETA": "beta",
    "SE": "sebeta",
    "LOG10P": "pval",
    "TEST": "test",
}

# "BSEX" is the value tested as an interaction variable in regenie.
interaction_aliases = {"BSEX": "sex"}
