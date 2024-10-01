from flask import current_app, send_from_directory
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
    
    def __init__(self):
        self.data = {}
        phenotype_file_dir = current_app.config['PHENOTYPES_DIR']
        phenotype_file_path = os.path.join(phenotype_file_dir, 'phenotypes.json')

        with open(phenotype_file_path, 'r') as file:
            self.data = json.load(file)
    
    def get_phenotypes(self):
        return self.data
    
class Pheno():
    
    # TODO: in the future, it would be a thousand times better 
    # to have a sqlite3 nosql database with all the manhattan jsons inside,
    # so we could query the database instead of reading the json every single time
    #pheno = get_pheno():
    
    # it would also likely be better to pre-populate the pheno dict for this purpose
    
    # but for now, send_from_directory is likely the fastest way
    def __init__(self):
        self.pheno = {}

    
    def get_pheno(self, phenocode):
        response = send_from_directory(current_app.config['MANHATTAN_DIR'], f"{phenocode}.json")
        return response

# TODO : create functionality for getting information for phewas page
class Variant():
    def __init__(self):
        self.variants = {}
    
    def get_variant(self, variant_code):
        return self.variants[variant_code]
    