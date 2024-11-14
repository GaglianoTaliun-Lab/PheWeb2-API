import os.path
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')

BASE_DIR = os.getenv('BASE_DIR')

PHENOTYPES_DIR = os.path.join(BASE_DIR)
MANHATTAN_DIR = os.path.join(BASE_DIR, "manhattan")
QQ_DIR = os.path.join(BASE_DIR, "qq")
PHENO_GZ_DIR = os.path.join(BASE_DIR, "pheno_gz")
BEST_OF_PHENO_DIR = os.path.join(BASE_DIR, "best_of_pheno")
PHEWAS_MATRIX_DIR = os.path.join(BASE_DIR, "matrix-stratified")

## Manhattan / top-hits / top-loci config
MANHATTAN_NUM_UNBINNED = 500
MANHATTAN_PEAK_MAX_COUNT = 500
MANHATTAN_PEAK_PVAL_THRESHOLD = 1e-6
MANHATTAN_PEAK_SPRAWL_DIST = 200_000
MANHATTAN_PEAK_VARIANT_COUNTING_PVAL_THRESHOLD = 5e-8

PVAL_IS_NEGLOG10 = True

# CORS_ORIGINS = ['http://localhost:8099']
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')
