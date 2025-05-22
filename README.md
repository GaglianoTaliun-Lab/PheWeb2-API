# PheWeb 2.0 API
This is an implementation of the data model and API for [PheWeb 2.0](https://github.com/GaglianoTaliun-Lab/PheWeb2.0/tree/main) - an enhanced version of the original [PheWeb](https://github.com/statgen/pheweb) tool for interactive querying, visualizing, and sharing summary-level results from GWAS/PheWAS studies, which offers intuitive and efficient support for stratified results. In PheWeb 2.0, we de-coupled the data model and API from the UI to improve code maintenance and re-usability and allow new features such as on-the-fly GWAS/PheWAS results querying by other external resources and applications. 

## Dependencies
Python 3.12+ is required (all python package dependencies can be found in the `requirements.txt`)
Linux-Based Environment

## Installation
```
python -m venv .venv
source .venv/bin/activate
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

### Interaction Testing

If you wish to pre-process interaction results via Regenie output, you need to set 'interaction_aliases' to the value you gave regenie for the interaction testing and remap it to a value of your choice.

See sample_config.py for an example.

### Pheno-list{.csv, .json}

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


To pre-process all files to properly work with the backend server, run

`pheweb process`

in the base directory of PheWeb. (Parent directory of preprocessing/)

You must have pheno-list.json inside the base directory.

## Runtime Data
After pre-processing, you will get a folder called `generated_by_pheweb/`, which contains the data for the API application.

Ensure these folders (with data) are present before running the backend / API.

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


