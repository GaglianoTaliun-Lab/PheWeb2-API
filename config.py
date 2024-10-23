import os.path
from .config import BASE_DIR

#BASE_DIR = os.path.join(os.sep, 'home', 'justb11', "scratch", "sex-stratified-pheweb", "PheWeb2.0-API", "data")
#BASE_DIR = os.path.join(os.sep, 'home', 'justb11', "projects", "def-gsarah", "justb11", "sex-stratified", "PheWeb2.0-API", "data")

PHENOTYPES_DIR = os.path.join(BASE_DIR)
MANHATTAN_DIR = os.path.join(BASE_DIR, "manhattan")
QQ_DIR = os.path.join(BASE_DIR, "qq")
PHENO_GZ_DIR = os.path.join(BASE_DIR, "pheno_gz")
BEST_OF_PHENO_DIR = os.path.join(BASE_DIR, "best_of_pheno")

## Manhattan / top-hits / top-loci config
MANHATTAN_NUM_UNBINNED = 500
MANHATTAN_PEAK_MAX_COUNT = 500
MANHATTAN_PEAK_PVAL_THRESHOLD = 1e-6
MANHATTAN_PEAK_SPRAWL_DIST = 200_000
MANHATTAN_PEAK_VARIANT_COUNTING_PVAL_THRESHOLD = 5e-8

CORS_ORIGINS = ['http://localhost:8090']
