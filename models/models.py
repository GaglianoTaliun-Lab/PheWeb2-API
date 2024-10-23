from flask import current_app, send_from_directory, send_file
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
    
    def __init__(self, data):
        self.data = data

    def get_phenotypes(self):
        return self.data
    
class Pheno():
    
    # TODO: in the future, it would be a thousand times better 
    # to have a sqlite3 nosql database with all the manhattan jsons inside,
    # so we could query the database instead of reading the json every single time
        
    # but for now, send_from_directory is likely the fastest way
    
    def __init__(self, data = []):
        self.pheno = {}
        self.phenolist = data
        
    def get_phenolist(self, phenocode):
        
        if not phenocode:
            return self.phenolist
        
        # we can turn self.phenolist into a dict with keys somehow being stratifications to optimize O(n) -> O(1)
        specified_phenos = [pheno_info for pheno_info in self.phenolist if pheno_info['phenocode']==phenocode]
        return specified_phenos
                
    def get_pheno(self, phenocode):
        response = send_from_directory(current_app.config['MANHATTAN_DIR'], f"{phenocode}.json")
        return response
    
    def get_qq(self, phenocode):
        response = send_from_directory(current_app.config['QQ_DIR'], f"{phenocode}.json")
        return response
    
    # TODO: filtering logic
    def get_pheno_filtered(self, phenocode, chosen_variants1, chosen_variants2 = None):
        
        # TODO : we will get the manhattan.json but only take the variants present in chosen_variants
        response = send_from_directory(current_app.config['BEST_OF_PHENO_DIR'], f"{phenocode}")
        return response
    
    def get_sumstats(self, phenocode):
        response = send_file(current_app.config['PHENO_GZ_DIR'] + f"/{phenocode}.gz",
                                        as_attachment=True,
                                        download_name=f'phenocode-{phenocode}.tsv.gz')
        return response

# TODO : create functionality for getting information for phewas page
class Variant():
    def __init__(self):
        self.variants = {}
    
    def get_variant(self, variant_code):
        return self.variants[variant_code]
    
    
# functions to create class (factory pattern)
def create_phenotypes() -> Phenotypes:
        
    data = send_from_directory(current_app.config['PHENOTYPES_DIR'], 'phenotypes.json' )
        
    return Phenotypes(data)

def create_phenolist() -> Pheno:

    try:
        with open(os.path.join(current_app.config['PHENOTYPES_DIR'], 'pheno-list.json')) as f:
            data = json.load(f)

    except Exception as e:
        # TODO: logger instead of print?
        print(e)
        return None
    
    return Pheno(data)

def create_variant() -> Variant:
    
    return Variant()
    