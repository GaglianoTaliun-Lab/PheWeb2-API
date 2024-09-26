from flask import current_app
import os
import json


def get_phenotypes():
    phenotype_file_dir = current_app.config['PHENOTYPES_DIR']
    phenotype_file_path = os.path.join(phenotype_file_dir, 'phenotypes.json')

    with open(phenotype_file_path, 'r') as file:
        data = json.load(file)
    
    return data