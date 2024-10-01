from flask import current_app
import os
import json

"""
My eventual aspiration is to have an SQLite3 database for all these 
data, which will use classes such as these for insertion, get, etc..

For now, while the classes aren't necessary, it creates a decent organizational
structure that we can follow

In addition, these classes allow pre-loading of most data, thereby only having latency
for the query part (again, in theory)
"""

class Phenotypes():
    
    data = {}
    phenotype_file_dir = current_app.config['PHENOTYPES_DIR']
    phenotype_file_path = os.path.join(phenotype_file_dir, 'phenotypes.json')

    with open(phenotype_file_path, 'r') as file:
        data = json.load(file)
    
    def get_phenotypes(self):
        return self.data
    
# TODO: implement pheno class
class Pheno():
    
    pheno = []
    #pheno = get_pheno():
    
    def get_pheno(self, variant_code):
        return self.variants[variant_code]

# TODO : create functionality for getting information for phewas page
class Variants():
    
    variants = []
    #variants = get_variants():
    
    def get_variant(self, variant_code):
        return self.variants[variant_code]
    