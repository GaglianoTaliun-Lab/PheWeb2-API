import argparse, os
import polars as pl
from tqdm import tqdm
import re

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
    
    step1_folder = os.path.join(folder, "genomic_predictions")
    step2_folder = os.path.join(folder, "GWAS", "results")
    
    for root, _, files in tqdm(os.walk(step1_folder), desc="Processing step 1 files"):
        for file in files:
            parts = file.split(".")
            
            # only take the log file
            if (parts[-1] != "log"):
                continue
            
            # get the number of observations
            if (not args.binary):

                pattern = re.compile(f"'{parts[0]}': (\d+) observations")
                
                with open(os.path.join(root, file), 'r') as f:
                    for line in f:
                        match = pattern.search(line)
                        
                        if match:

                            num_samples_list.append(match.group(1))
                            num_cases_list.append(None)
                            num_controls_list.append(None)
                            
                            if args.interaction:
                                num_samples_list.append(match.group(1))
                                num_cases_list.append(None)
                                num_controls_list.append(None)

                            break
            
            elif (args.binary):
                pattern = re.compile(f"'{parts[0]}': (\d+) cases and (\d+) controls")
                
                with open(os.path.join(root, file), 'r') as f:
                    for line in f:
                        match = pattern.search(line)
                        
                        if match:
                            num_cases_list.append(match.group(1))
                            num_controls_list.append(match.group(2))
                            num_samples_list.append(match.group(1) + match.group(2))

                            if args.interaction:
                                num_cases_list.append(match.group(1))
                                num_controls_list.append(match.group(2))
                                num_samples_list.append(match.group(1) + match.group(2))
                                
                            break

    
    for root, _, files in tqdm(os.walk(step2_folder), desc= "Processing step 2 files"):
        for file in files:
            phenocode_list.append(file.split('.')[0])
            file_list.append(os.path.join(root, file))
            
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

    parser.add_argument('-f', '--folder', type = str, required = True, help="Name of the top level results folder for both steps.\n* E.i. should only contain genomic_predictions/ and GWAS/")
    parser.add_argument('-c', '--csv', type = str, default=None, required = False, help="Name of pheno-list.csv where results will be appended to. Default: will create one.")
    parser.add_argument('-l', '--labels', type=str, default=None, required=False, help="File containing all labels and phenocodes as seperate columns.")
    parser.add_argument('-ct', '--categories', type=str, default=None, required = False, help="A file containing categories for given traits.")
    parser.add_argument('-b', '--binary', action='store_true', help="Are the files binary? No flag if continuous")
    parser.add_argument('-s', '--sex', type = str, default=None, required = False, help="Sex stratification (e.g. male). Default = 'both'")
    parser.add_argument('-a', '--ancestry', type = str, default=None, required = False, help="Ancestry stratification (e.g. european). Default = 'european'")
    parser.add_argument('-i', '--interaction', type = str, default=None, required = False, help="Interaction variable (e.g. BSEX). Default = '' ")
    parser.add_argument('-o', '--output', type=str, default="", required=False, help="Output folder. Default is current folder.")

    args = parser.parse_args()
    
    df = main(args)
    
    # todo - check if we need to overrite the csv
    df.write_csv(os.path.join(args.output, "pheno-list.csv"), separator=",")