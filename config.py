import os.path

# This is the parent directory for PheWeb 2, which contains the `config.py` file.
PHEWEB_BASE_DIR = os.path.join(os.path.dirname(__file__))

# By default, the data ingested into PheWeb 2 is stored in the `{PHEWEB_BASE_DIR}/generated-by-pheweb`  directory.
# If you would like to change this, please provide the full path to your preferred alternative directory.
PHEWEB_DATA_DIR = os.path.join(PHEWEB_BASE_DIR, "generated-by-pheweb")
#PHEWEB_DATA_DIR = '/full/path/to/some/other/dir/'

# Please specify the version of the human genome build used for your data. The default version is GRCh38 (Build 38).
HG_BUILD_NUMBER = 38

# Please specify the dbSNP version for mapping to rsIDs
DBSNP_VERSION = 157

# Please specify the GENOCODE version for mapping to genes 
GENCODE_VERSION = 48

# If your data includes information on genotype imputation quality, please specify your desired threshold for filtering GWAS results. Variants with an imputation quality score below this threshold will be excluded during data ingestion.
MIN_IMP_QUALITY = 0.3

# Please specify the value in the TEST column of your GWAS files that indicates the main effect of the tested variant. For Regenie and PLINK2, this value should be set to “ADD” to denote rows with an additive effect. If Regenie was executed with the –interaction option, then “ADD-CONDTL” can also be used.
ASSOC_TEST_NAME = ["ADD", "ADD-CONDTL"]

# Please specify the threshold for variant minor allele frequency (MAF). Variants with a MAF below this threshold will be excluded during data ingestion.
ASSOC_MIN_MAF = 0.0

# Please specify the value in the TEST column of your GWAS files that indicates the interaction effect between the genotype and the interacting variable (e.g., sex). This value will depend on the specific name of the interacting variable in your dataset.
INTERACTION_TEST_NAME = "ADD-INT_SNPxBSEX=2"

# Please specify the threshold for minor allele count (MAC) for variants tested for interaction effects. Interaction test results for variants with a MAC below this threshold will be excluded during data ingestion. This threshold is study-dependent and is typically set to correspond to a much higher MAF than that in ASSOC_MIN_MAF.
INTERACTION_MIN_MAC = 160

# This parameter functions similarly to INTERACTION_MIN_MAC but is measured on the minor allele frequency (MAF) scale. Only one of the two parameters, INTERACTION_MIN_MAC or INTERACTION_MIN_MAF, may be set at any given time.
#INTERACTION_MIN_MAF = 0.05

# Set this to True if you have stratified GWAS results (default). Otherwise, set it to False.
ENABLE_STRATIFICATIONS = True



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

