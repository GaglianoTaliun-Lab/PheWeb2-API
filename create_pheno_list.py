import argparse, os
import polars as pl
from tqdm import tqdm
import re
import pandas as pd

def main(args : dict) -> None:
    
    folder = args.folder
    
    # read in categories if file exists
    if (args.categories):
        cats = pl.read_csv(
            args.categories,
            schema_overrides={
                "phenocode" : pl.Utf8,
                "category" : pl.Utf8
            }
        )
        
    if (args.labels):
        labels = pl.read_csv(
            args.labels,
            quote_char='"',
            encoding="utf8-lossy"
        )
        
    phenocode_list = []
    file_list = []
    num_samples_list = []
    num_cases_list = []
    num_controls_list = []
    interaction_list = []
    sex_list = []
    ancestry_list = []
    
    # step1_folder = os.path.join(folder, "genomic_predictions")
    # step2_folder = os.path.join(folder, "GWAS", "results")
    
    # for root, _, files in tqdm(os.walk(step1_folder), desc="Processing step 1 files"):
    #     for file in files:
    #         parts = file.split(".")
            
    #         # only take the log file
    #         if (parts[-1] != "log"):
    #             continue
            
    #         # get the number of observations
    #         if (not args.binary):

    #             pattern = re.compile(f"'{parts[0]}': (\d+) observations")
                
    #             with open(os.path.join(root, file), 'r') as f:
    #                 for line in f:
    #                     match = pattern.search(line)
                        
    #                     if match:

    #                         num_samples_list.append(match.group(1))
    #                         num_cases_list.append(None)
    #                         num_controls_list.append(None)
                            
    #                         if args.interaction:
    #                             num_samples_list.append(match.group(1))
    #                             num_cases_list.append(None)
    #                             num_controls_list.append(None)

    #                         break
            
    #         elif (args.binary):
    #             pattern = re.compile(f"'{parts[0]}': (\d+) cases and (\d+) controls")
                
    #             with open(os.path.join(root, file), 'r') as f:
    #                 for line in f:
    #                     match = pattern.search(line)
                        
    #                     if match:
    #                         num_cases_list.append(match.group(1))
    #                         num_controls_list.append(match.group(2))
    #                         num_samples_list.append(match.group(1) + match.group(2))

    #                         if args.interaction:
    #                             num_cases_list.append(match.group(1))
    #                             num_controls_list.append(match.group(2))
    #                             num_samples_list.append(match.group(1) + match.group(2))
                                
    #                         break

    # read in phenotype table
    # TODO: we need the sample size file as an input and should not recalculate it here!
    phenotype_df = pd.read_csv(args.phenotable, sep="\s+")
    print(f'phenotype_df.head(1): {phenotype_df.head(1)}')
    print(f'phenotype_df.shape: {phenotype_df.shape}')
    covariates_df = pd.read_csv(args.covariates, sep="\s+")
    print(f'covariates_df.shape: {covariates_df.shape}')

    filtered_phenotype_df = phenotype_df[phenotype_df['IID'].isin(covariates_df['IID'])].reset_index(drop=True)
    print(f'filtered_phenotype_df.shape: {filtered_phenotype_df.shape}')

    for root, _, files in tqdm(os.walk(folder), desc= "Processing GWAS results files"):
        for file in files:
            phenotype_name = file.split('.')[0]
            if args.test:
                top20_phenocodes = pd.read_csv(args.test, header=None)[0].astype(str).tolist()
                if phenotype_name not in top20_phenocodes:
                    continue
            phenocode_list.append(phenotype_name)
            file_list.append(os.path.join(root, file))

            if phenotype_name in phenotype_df.columns:
                if args.binary:
                    ... # TODO: add binary case and control counts
                else:
                    num_samples_list.append(filtered_phenotype_df[phenotype_name].notna().sum())
                    num_cases_list.append(None)
                    num_controls_list.append(None)
                    if args.interaction:
                        num_samples_list.append(filtered_phenotype_df[phenotype_name].notna().sum())
                        num_cases_list.append(None)
                        num_controls_list.append(None)
            else:
                raise ValueError(f"Phenotype {phenotype_name} not found in phenotype table.")
            
            ancestry_list.append(args.ancestry)
            interaction_list.append(None)
            sex_list.append(args.sex)
            
            if args.interaction:
                phenocode_list.append(file.split('.')[0])
                file_list.append(os.path.join(root, file))
                
                ancestry_list.append(args.ancestry)
                interaction_list.append(args.interaction)
                sex_list.append(args.sex)
                
    df = pl.DataFrame(
        {
            "phenocode" : phenocode_list,
            "assoc_files" : file_list,
            "num_samples" : num_samples_list,
            "num_cases" : num_cases_list,
            "num_controls" : num_controls_list,
            "interaction" : interaction_list,
            "stratification.sex" : sex_list,
            "stratification.ancestry" : ancestry_list,
        }
    ) 
    
    if (args.categories):
        df = df.join(cats, on="phenocode", how="left")
        
    if (args.labels):
        df = df.join(labels, on="phenocode", how="left")
        
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-f', '--folder', type = str, required = True, help="Name of the folder containing the GWAS results.")
    parser.add_argument('-p', '--phenotable', type = str, required = True, help="Name of the phenotype.txt file that store phenotype information for GWAS")
    parser.add_argument('-cv', '--covariates', type = str, default=None, required = True, help="Name of the covariates.txt file that store covariates information for GWAS")
    parser.add_argument('-c', '--csv', type = str, default="pheno-list.csv", required = False, help="Name of pheno-list.csv where results will be appended to. Default: will create one.")
    parser.add_argument('-l', '--labels', type=str, default=None, required=False, help="File containing all labels and phenocodes as seperate columns.")
    parser.add_argument('-ct', '--categories', type=str, default=None, required = False, help="A file containing categories for given traits.")
    parser.add_argument('-b', '--binary', action='store_true', help="Are the files binary? No flag if continuous")
    parser.add_argument('-s', '--sex', type = str, default='combined', required = False, help="Sex stratification (e.g. male). Default = 'combined'")
    parser.add_argument('-a', '--ancestry', type = str, default='european', required = False, help="Ancestry stratification (e.g. european). Default = 'european'")
    parser.add_argument('-i', '--interaction', type = str, default=None, required = False, help="Interaction variable (e.g. BSEX). Default = '' ")
    parser.add_argument('-o', '--output', type=str, default="", required=False, help="Output folder. Default is current folder.")
    parser.add_argument('-t', '--test', type=str, default=None, required=False, help="List of phenotypes that used to generate the top 20 phenotypes for testing")

    args = parser.parse_args()
    
    df = main(args)
    
    # todo - check if we need to overrite the csv
    df.write_csv(os.path.join(args.output, args.csv), separator=",")
    
    
# Example running: 

"""
python create_pheno_list.py -f /home/justb11/scratch/sex-stratified-pheweb/Regenie/results/continuous/both_2 -l phenocode_labels.csv -ct pheno_categories.csv -i BSEX
"""
