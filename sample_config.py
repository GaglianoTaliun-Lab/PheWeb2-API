import os.path

# Please create your own configuration file and do not overwrite this file 

BASE_DIR = os.path.join(os.sep, 'PATH', 'TO', "YOUR", "DATA", "DIR")

PHENOTYPES_DIR = os.path.join(BASE_DIR)
MANHATTAN_DIR = os.path.join(BASE_DIR, "manhattan")
QQ_DIR = os.path.join(BASE_DIR, "qq")


CORS_ORIGINS = ['http://PATH/TO/YOUR/UI']
