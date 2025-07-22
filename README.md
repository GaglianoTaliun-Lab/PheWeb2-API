# PheWeb 2.0 API
This is an implementation of the data model and API for [PheWeb 2.0](https://github.com/GaglianoTaliun-Lab/PheWeb2.0/tree/main) — an enhanced version of the original [PheWeb](https://github.com/statgen/pheweb) web-based tool for interactive querying, visualizing, and sharing summary-level results from genome-wide and phenome-wide association studies (GWAS/PheWAS), which offers intuitive and efficient support for stratified analysis results. PheWeb 2.0 decouples the data model and API from the user interface (UI) to improve code maintenance and reusability and allow results querying by other external resources and applications. 
 
> [!NOTE]
> The code was developed and tested with Python 3.12+ on Linux-based OS.
 
## 1. Installation

Clone this repository:
```
git clone https://github.com/GaglianoTaliun-Lab/PheWeb2.0-API.git
python -m venv .venv
```

Create and activate Python virtual environment:
```
python -m venv .venv
source .venv/bin/activate
```

Install the required Python packages:
```
pip install -r requirements.txt
```
 
## Preprocessing


 
### GWAS Summary Statistics
Currently, all preprocessing functions require output from [Regenie](https://rgcgithub.github.io/regenie/).

Specifically, summary statisitcs must contain:

| column description | name       | allowed values              |
| ------------------ | ---------- | --------------------------- |
| Chromosome         | CHROM      | 1-23                        |
| Position           | GENPOS     | integer                     |
| Reference Allele   | ALLELE0    | must match reference genome |
| Effect Allele      | ALLELE1    | anything                    |
| Beta               | BETA       | float                       |
| Standard Error     | SE         | float                       |
| Log-10 P-value     | LOG10P     | float                       |
| Statistical Test   | TEST       | anything                    | 

Any field can be null if it is one of ['', '.', 'NA', 'N/A', 'n/a', 'nan', '-nan', 'NaN', '-NaN', 'null', 'NULL']. If a required field is null, the variant gets dropped.
 
### Imputation Quality Filtering
In the preprocessing, you can filter out variants that have imputation quality lower than a customized threshold. To implement this, you can use specific field from the GWAS results (e.g., the INFO field in REGENIE output). You can specify the imputation quality field and threshold in the `config.py` by
```
MIN_IMP_QUALITY = # your imputation quality threshold
field_aliases = {
    ...
    # Add this field if you have imputation quality scores in the GWAS results
    # e.g., if the imputation quality field in the GWAS results is called 'INFO'
    "INFO": "imp_quality",
    ...
}
```
***
However, we strongly recommend you to access the imputation quality scores from external files, especially if you are using REGENIE to generate the GWAS results. We strongly recommend to use the VCF files (input of GWAS) as the source of the imputation quality scores.
***
You can set it up in the `config.py` by
```
MIN_IMP_QUALITY = # your imputation quality threshold
field_aliases = {
    ...
    # Start your custom field (e.g. imp_quality) with "file://" to load from a file (accept vcf files for imputation quality). Separate the file path the the field of interest by ','
    "file://path/file.vcf.gz,R2": "imp_quality",
    ...
}
```
 
### Interaction Testing

If you wish to pre-process interaction results via Regenie output, you need to set 'interaction_aliases' to the value you gave regenie for the interaction testing and remap it to a value of your choice.

See sample_config.py for an example.

### Pheno-list{.csv, .json}

Like the `config.py` file, a pheno-list.json file MUST be in the base directory of the PheWeb-API before running any command.
- `PheWeb2.0-API/config.py`
- `PheWeb2.0-API/pheno-list.json`

We highly recommend creating a pheno-list.csv file, then converting to pheno-list.json. 


Here are the required and optional columns for the pheno-list.csv file:
 
| column description                                  | value         | allowed values                      | required? |
| --------------------------------------------------- | ------------- | ----------------------------------- | --------- |
| Phenotype Code                                      | phenocode     | string                              | true      |
| Phenotype Description                               | phenostring   | string                              | true      |
| Location of summary statistics                      | assoc_files   | string                              | true      |
| Number of tested samples / participants             | num_samples   | int                                 | false     |
| Number of tested cases                              | num_cases     | int                                 | false     |
| Number of tested controls                           | num_controls  | int                                 | false     |
| Category of trait                                   | category      | float                               | false     |
| Variable of Interaction Testing                     | interaction   | string                              | false     |
| Category of stratification (Can be more than one)   | interaction   | "stratification.*" (where *=string) | false     |

Refer to pheno-list-example.csv for an example.
Then with 'pheno-list.csv', run:

`pheweb phenolist import-phenolist "/path/to/pheno-list.csv"`

to create `pheno-list.json`.


To pre-process all files to properly work with the backend server, run:

`pheweb process`

To manually enable the autocomplete functionality of searching variant id or rsid, please run:

`pheweb generate-autocomplete-db`

to create `autocomplete.db`. Alternative option: the `autocomplete.db` will be created when you first run the api.

## Runtime Data
After pre-processing, these folders (with data) need to be present before running.

```
CLSA_PheWeb_data
└── generated_by_pheweb
    ├── manhattan
        ├── ... 
    ├── qq
        ├── ...
    ├── phenotypes.json 
    ├── top_hits.json 
    ├── ...
```

The paths to the runtime data needs to be specified in the config.py
```py
BASE_DIR = os.path.join(os.sep, 'var', 'local', 'CLSA_PheWeb_data', 'generated_by_pheweb')

PHENOTYPES_DIR = os.path.join(BASE_DIR)
...
```
please refer the `sample_config.py` for more examples.
 

## Running Backend Server
```
pheweb-run
```

get data through http://localhost:9099/PATH/TO/ROUTES/

e.g. to view phenotype table data, go to http://localhost:9099/phenotypes
 
## Documentation

To see all available API routes, visit http://localhost:9099/ (or the location of your backend API instance).

Documentation was created with [Flask-RESTX](https://flask-restx.readthedocs.io/en/latest/).


