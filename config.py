import os.path
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")

BASE_DIR = os.getenv("BASE_DIR")

PHENOTYPES_DIR = os.path.join(BASE_DIR)
MANHATTAN_DIR = os.path.join(BASE_DIR, "manhattan")
QQ_DIR = os.path.join(BASE_DIR, "qq")
PHENO_GZ_DIR = os.path.join(BASE_DIR, "pheno_gz")
BEST_OF_PHENO_DIR = os.path.join(BASE_DIR, "best_of_pheno")
PHEWAS_MATRIX_DIR = os.path.join(BASE_DIR, "matrix-stratified")
INTERACTION_DIR = os.path.join(BASE_DIR, "interaction")

## Manhattan / top-hits / top-loci config
MANHATTAN_NUM_UNBINNED = 500
MANHATTAN_PEAK_MAX_COUNT = 500
MANHATTAN_PEAK_PVAL_THRESHOLD = 1e-6
MANHATTAN_PEAK_SPRAWL_DIST = 200_000
MANHATTAN_PEAK_VARIANT_COUNTING_PVAL_THRESHOLD = 5e-8

# Filtering parameters
MIN_IMP_QUALITY = 0.3
INTERACTION_MAC_THRESHOLD = 160

# Path to the file containing the R2/Imputation Quality values (optional)
R2_FILE = os.getenv("R2_DIR")

hg_build_number = 38

stratified = True

pval_is_neglog10 = True

field_aliases = {
    "CHROM": "chrom",
    "GENPOS": "pos",
    "ALLELE0": "ref",
    "ALLELE1": "alt",
    "A1FREQ": "af",
    # Add this field if you have imputation quality scores in the GWAS results
    # "INFO": "imp_quality",
    # Start your custom field (e.g. imp_quality) with "file://" to load from a file (accept pvar or vcf files)
    # "file://path/file.pvar,R2": "imp_quality",
    f"file://{R2_FILE},R2": "imp_quality",
    "N": "n_samples",
    "BETA": "beta",
    "SE": "sebeta",
    "LOG10P": "pval",
    "TEST": "test",
}

interaction_aliases = {"sex": "sex"}
