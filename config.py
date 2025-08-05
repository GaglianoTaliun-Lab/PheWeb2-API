import os.path

# This is the parent directory for PheWeb 2, which contains the `config.py` file.
PHEWEB_BASE_DIR = os.path.join(os.path.dirname(__file__))

# By default, the data ingested into PheWeb 2 is stored in the `{PHEWEB_BASE_DIR}/generated-by-pheweb`  directory.
# If you would like to change this, please provide the full path to your preferred alternative directory.
PHEWEB_DATA_DIR = os.path.join(PHEWEB_BASE_DIR, "generated-by-pheweb")
#PHEWEB_DATA_DIR = '/full/path/to/some/other/dir/'

# The configuration variables listed below are utilized internally and do not require any modifications.
PHENOTYPES_DIR = os.path.join(PHEWEB_DATA_DIR)
MANHATTAN_DIR = os.path.join(PHEWEB_DATA_DIR, "manhattan")
QQ_DIR = os.path.join(PHEWEB_DATA_DIR, "qq")
PHENO_GZ_DIR = os.path.join(PHEWEB_DATA_DIR, "pheno_gz")
BEST_OF_PHENO_DIR = os.path.join(PHEWEB_DATA_DIR, "best_of_pheno")
PHEWAS_MATRIX_DIR = os.path.join(PHEWEB_DATA_DIR, "matrix-stratified")
INTERACTION_DIR = os.path.join(PHEWEB_DATA_DIR, "interaction")
SITES_DIR = os.path.join(PHEWEB_DATA_DIR, "sites")

# The configuration variables listed below are used internally for generating Manhattan/Miami plots and do not require any modifications.
MANHATTAN_NUM_UNBINNED = 500
MANHATTAN_PEAK_MAX_COUNT = 500
MANHATTAN_PEAK_PVAL_THRESHOLD = 1e-6
MANHATTAN_PEAK_SPRAWL_DIST = 200_000
MANHATTAN_PEAK_VARIANT_COUNTING_PVAL_THRESHOLD = 5e-8

# Please specify the version of the human genome build used for your data. The default version is GRCh38 (Build 38).
HG_BUILD_NUMBER = 38

# Please specify the dbSNP version for mapping to rsIDs
DBSNP_VERSION = 157

# Please specify the GENOCODE version for mapping to genes 
GENCODE_VERSION = 48

# Filtering parameters
MIN_IMP_QUALITY = 0.3
INTERACTION_MAC_THRESHOLD = 160


stratified = True

pval_is_neglog10 = True

field_aliases = {
    "CHROM": "chrom",
    "GENPOS": "pos",
    "ALLELE0": "ref",
    "ALLELE1": "alt",
    "A1FREQ": "af",
    "N": "n_samples",
    "BETA": "beta",
    "SE": "sebeta",
    "LOG10P": "pval",
    "TEST": "test",
    # Add this field if you have imputation quality scores in the GWAS results
    "INFO": "imp_quality",
    # Start your custom field (e.g. imp_quality) with "file://" to load from a file (accept pvar or vcf files)
    # "file://path/file.pvar,R2": "imp_quality",

}

interaction_aliases = {"BSEX=2": "sex"}

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")

