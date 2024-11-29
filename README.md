# PheWeb 2.0 API
This is an implementation of the data model and API for [PheWeb 2.0](https://github.com/GaglianoTaliun-Lab/PheWeb2.0/tree/main) - a new version of the original [PheWeb](https://github.com/statgen/pheweb) tool for interactive querying, visualizing, and sharing summary-level results from GWAS/PheWAS studies. In the PheWeb 2.0, we de-coupled the data model and API from the UI to improve code maintenance and re-usability and allow new features such as on-the-fly GWAS/PheWAS results querying by other external resources and applications.

## Running
```
python app.py
```
get data through http://localhost:9099/ui/PATH/TO/ROUTES/
e.g. to view phenotype table data, go to http://localhost:9099/ui/phenotypes


## Dependencies

### Runtime Data
The runtime data on disk needs to be present before running.

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
please refer the `sample_config.py` for more examples


# Preprocessing

To run the data pre-processing, run (in the same folder as setup.py)

`pip install -e .`

with python >=3.12


Then with your 'pheno-list.csv' properly filled out (see pheno-list-example.csv)`

run

`pheweb phenolist import-phenolist "/path/to/pheno-list.csv"`


Then:

`pheweb process`


# Documentation

In order to keep an orderly documention of this API, we have used Flask RESTX (https://github.com/python-restx/flask-restx)