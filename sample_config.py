import os.path

# Please create your own configuration file and do not overwrite this file 

BASE_DIR = os.path.join(os.sep, 'PATH', 'TO', "YOUR", "DATA", "DIR")

PHENOTYPES_DIR = os.path.join(BASE_DIR)
MANHATTAN_DIR = os.path.join(BASE_DIR, "manhattan")
QQ_DIR = os.path.join(BASE_DIR, "qq")
PHENO_GZ_DIR = os.path.join(BASE_DIR, "pheno_gz")
BEST_OF_PHENO_DIR = os.path.join(BASE_DIR, "best_of_pheno")

CORS_ORIGINS = ['http://PATH/TO/YOUR/UI']
