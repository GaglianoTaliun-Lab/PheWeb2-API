import os.path


# SECTION A: Data location
# ================================================
 
# This is the parent directory for PheWeb 2, which contains the `config.py` file.
PHEWEB_BASE_DIR = os.path.join(os.path.dirname(__file__))

# By default, the data ingested into PheWeb 2 is stored in the `{PHEWEB_BASE_DIR}/generated-by-pheweb`  directory.
# If you would like to change this, please provide the full path to your preferred alternative directory.
PHEWEB_DATA_DIR = os.path.join(PHEWEB_BASE_DIR, "generated-by-pheweb")
#PHEWEB_DATA_DIR = '/full/path/to/some/other/dir/'


# SECTION B: Public databases
# ================================================

# Please specify the version of the human genome build used for your data. The default version is GRCh38 (Build 38).
HG_BUILD_NUMBER = 38

# Please specify the dbSNP version for mapping to rsIDs
DBSNP_VERSION = 154

# Please specify the GENOCODE version for mapping to genes 
GENCODE_VERSION = 37


# SECTION C: Data ingestion
# ===============================================

# Set number of parallel processes for data ingestion on a single node
NUM_PROCS = 8

# Please specify the value in the "test" column of your GWAS files that indicates rows with the main effect of the tested variant. For Regenie and PLINK2, this value should be set to “ADD” to denote rows with an additive effect. If Regenie was executed with the –interaction option, then “ADD-CONDTL” can also be used.
ASSOC_TEST_NAME = ["ADD", "ADD-CONDTL"]

# Please specify the threshold for variant minor allele frequency (MAF). Variants with a MAF below this threshold will be excluded during data ingestion.
ASSOC_MIN_MAF = 0.0

# Please specify the value in the "test" column of your GWAS files that indicates rows with the interaction effect between the genotype and the interacting variable (e.g., sex). This value will depend on the specific name of the interacting variable in your dataset.
INTERACTION_TEST_NAME = "ADD-INT_SNPxBSEX=2"

# Please specify the threshold for minor allele count (MAC) for variants tested for interaction effects. Interaction test results for variants with a MAC below this threshold will be excluded during data ingestion. This threshold is study-dependent and is typically set to correspond to a much higher MAF than that in ASSOC_MIN_MAF.
INTERACTION_MIN_MAC = 160

# This parameter functions similarly to INTERACTION_MIN_MAC but is measured on the minor allele frequency (MAF) scale. Only one of the two parameters, INTERACTION_MIN_MAC or INTERACTION_MIN_MAF, may be set at any given time.
#INTERACTION_MIN_MAF = 0.05

# Set this to True if you have stratified GWAS results (default). Otherwise, set it to False.
ENABLE_STRATIFICATIONS = True

# Set to `True` (default is `False`) if the p-values in your GWAS result files are already reported on a negative log10 scale.
PVAL_IS_NEGLOG10 = True

# If your data includes information on genotype imputation quality, please specify your desired threshold for filtering GWAS results. Variants with an imputation quality score below this threshold will be excluded during data ingestion.
MIN_IMP_QUALITY = 0.3

# Please provide a mapping from the field names in your GWAS files to the names used by PheWeb. For instance, an entry like `"CHROM": "chrom"` indicates that the chromosome name in your GWAS files is stored in the “CHROM” field.
FIELD_ALIASES = {
    "CHROM": "chrom", # Chromosome
    "GENPOS": "pos", # Position
    "ALLELE0": "ref", # Reference allele
    "ALLELE1": "alt", # Effect (tested) allele
    "A1FREQ": "af", # Frequency of the effect allele
    "N": "n_samples", # Number of samples
    "BETA": "beta", #  Effect size
    "SE": "sebeta", # Standard error of the effect
    "LOG10P": "pval", # P-value
    "TEST": "test", # Reported statistical test/model

    # If you have imputation quality scores saved in the GWAS results (e.g. in the "INFO" field), then you can map them as follows:
    "INFO": "imp_quality",
    # If you have imputation quality scores stored separately from your GWAS results, please begin your custom field with “file://” followed by the file name and the specific field name that contains the quality scores within it. Currently, this feature accepts PLINK2’s PVAR or VCF formats.
    # "file://path/file.pvar,R2": "imp_quality",
}

# SECTION D: Runtime parameters
# ===============================================

# Set to `True` to enable debug mode for data ingestion and API. Set `False` in the production mode.
ENABLE_DEBUG = False

# Set the host for the API endpoint (default is localhost)
HOST = '127.0.0.1'

# Set the port number for the API endpoint.
PORT = 9090

# Set the API URL prefix if applicable, e.g., when you are running the API behind a reverse proxy (e.g., using Apache).
API_URL_PREFIX = ""

# Set the number of workers to run API in parallel (default is 4).
NUM_API_WORKERS = 4

# Specify the comma-separated list of origins allowed to access the API. By default, all are allowed, i.e., '*'.
CORS_ORIGINS = '*'

# SECTION E: Internal parameters (no need to modify)
# ===============================================

# The configuration variables listed below are used internally for generating Manhattan/Miami plots and do not require any modifications.
MANHATTAN_NUM_UNBINNED = 500
WITHIN_PHENO_MASK_AROUND_PEAK = 500_000
BETWEEN_PHENO_MASK_AROUND_PEAK = 1_000_000
MANHATTAN_NUM_UNBINNED = 500
MANHATTAN_PEAK_MAX_COUNT = 500
MANHATTAN_PEAK_PVAL_THRESHOLD = 1e-6
MANHATTAN_PEAK_SPRAWL_DIST = 200_000
MANHATTAN_PEAK_VARIANT_COUNTING_PVAL_THRESHOLD = 5e-8
TOP_HITS_PVAL_CUTOFF = 1e-6
PHENO_CORRELATIONS_PVALUE_THRESHOLD = 0.05








