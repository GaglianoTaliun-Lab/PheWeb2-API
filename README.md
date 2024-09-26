# PheWeb2.0-API

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
/var/local/CLSA_PheWeb_data
└── runtime
    ├── phenotypes
        ├── phenotypes.json 
    ├── ...
```

The paths to the runtime data needs to be specified in the config.py
```py
BASE_DIR = os.path.join(os.sep, 'var', 'local', 'CLSA_PheWeb_data', 'runtime')

PHENOTYPES_DIR = os.path.join(BASE_DIR, 'phenotypes')
...
```
