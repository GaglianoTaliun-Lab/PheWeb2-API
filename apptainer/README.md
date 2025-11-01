# Use a container image to deploy PheWeb 2 API

The PheWeb 2 API container image is available through the [Docker Hub image repository](https://hub.docker.com/r/xiaoh11/pheweb2-api).
The sections below describe how to use it with [Apptainer](https://apptainer.org/). The process for [Docker](https://www.docker.com/) is very similar.

## 1. Download the latest image
```
mkdir -p PheWeb2-API
cd PheWeb2-API
apptainer pull pheweb2-api-latest.sif docker://xiaoh11/pheweb2-api:latest
```

## 2. Test it out using our small example data

1. Download our sample data to your PheWeb2-API directory:
   ```
   wget https://objets.juno.calculquebec.ca/swift/v1/AUTH_290e6dcc5e264b34b401f54358bd4c54/pheweb_example_data/example_regenie.tar.gz
   tar -xzvf example_regenie.tar.gz
   ```
   
2. Download the default configuration file to your PheWeb2-API directory:
   ```
   curl -O https://raw.githubusercontent.com/GaglianoTaliun-Lab/PheWeb2-API/main/config.py
   ```
   
   > **🚨 Important:** 
   > Please avoid modifying the default values in the config.py file when working with the example dataset. This file specifies the default versions of dbSNP (v157, genome build 38) and GENCODE (v48, genome build 38) databases. We host these versions on our servers to make your work easier and to ensure a faster workflow.
   
3. Download and import the example manifest file describing phenotypes inside your PheWeb2-API directory:
   ```
   curl -O https://raw.githubusercontent.com/GaglianoTaliun-Lab/PheWeb2-API/main/manifest-example.csv
   apptainer exec pheweb2-api-latest.sif pheweb2 phenolist import-phenolist manifest-example.csv
   ```
> [!NOTE]
> For these and subsequent `apptainer` commands using the small example data, we rely on `apptainer`'s default behavior of mounting the current working directory (i.e. PheWeb2-API). This ensures the container has access to the `config.py` configuration file and other input files. If, for some reason, it doesn't work, try explicitly mounting the current working directory adding the corresponding `-B` option e.g. ``apprainer exec -B `pwd` pheweb2-api-latest.sif pheweb2 ...``.
   
4. Ingest the example data into PheWeb2 (this can take some time):
   ```
   apptainer exec pheweb2-api-latest.sif pheweb2 process
   ```
   
5. Run automated tests of the API routes:
   ```
   apptainer exec pheweb2-api-latest.sif pytest /app/tests/test_routes.py -s -v
   ```
   
6. Launch PheWeb2 API endpoint which will be available at `http://127.0.0.1:9543`:
   ```
   apptainer exec pheweb2-api-latest.sif pheweb2 serve --host 127.0.0.1 --port 9543
   ```
   
7. To access the interactive API documentation, open your internet browser and navigate to http://localhost:9543/docs, assuming you are running it on the same machine at port 9543.


## 3. Run using your own data

Refer to the ["3. Run using your own data"](https://github.com/GaglianoTaliun-Lab/PheWeb2-API/tree/main?tab=readme-ov-file#3-run-using-your-own-data) section of the main documentation for instructions on preparing and ingesting your own data.

The main thing to remember when using a container image is that you need to make sure the necessary directories are accessible by `singularity` (or `docker`, if you're using that instead).

In particular, make sure that:
1. If you changed the default `PHEWEB_DATA_DIR` in `config.py`, remember you may need explicitly bind your new data directory in subsequent `apptainer` commands. For example:
  ```
  apptainer exec -B /path/to/my/pheweb/data/dir/ pheweb2-api-latest.sif pheweb2 ...
  ```
2. Make sure the directory with your input GWAS files, which are listed in your Manifest file, is also accessible within the container image (i.e. bind it using `-B /path/to/my/gwas/files/` option). 

