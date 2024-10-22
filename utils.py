import polars as pd
from flask import current_app

# extract variants from the given phenocode within the set parameters of min_maf and max_maf
def extract_variants(phenocode, min_maf, max_maf) -> list:

    
    # load best of file
    # it's just a tsv of max 100 000 rows so I think the best option would be polars (instead of pandas) for this.
    df = pd.read_csv(current_app.config['BEST_OF_PHENO'] + f"/{phenocode}", 
                    seperator = "\t",
                    schema = {'chrom' : int, 'pos' : int, 'ref': str, 'alt' : str, 'rsids' : str, 'nearest_genes' : str, 'pval': float, 'beta' : float, 'sebeta' : float, 'af' : float}
                    )
    
    print("called extract variants")
    print(df)
    return []