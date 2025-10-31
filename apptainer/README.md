# Deploy PheWeb 2 without installing from GitHub (using `apptainer` with minimal steps)
We released the Docker image file for strict version control. If you want to easily deploy the tool (e.g. to test it), please do the following steps:

## 1. Make sure you have `apptainer` installed on your machine

   If not, please refer to https://github.com/apptainer/apptainer/blob/main/INSTALL.md to install `apptainer`

   For any questions about using `apptainer`, please refer to their official documentation https://apptainer.org/docs/user/main/quick_start.html 

## 2. Build the apptainer image
   ```
   mkdir -p PheWeb2-API
   cd PheWeb2-API
   apptainer pull pheweb2-api-latest.sif docker://xiaoh11/pheweb2-api:latest
   ```

   If you prefer to build the apptainer image based on a def file, we also provided it in `./pheweb2api.def`

   You can copy this file to your machine and do
   ```
   apptainer build pheweb2-api-latest.sif PATH/TO/YOUR/pheweb2api.def
   ```


## 3. Download/Prepare the data

For testing, you can download our sample data
   ```
   wget https://objets.juno.calculquebec.ca/swift/v1/AUTH_290e6dcc5e264b34b401f54358bd4c54/pheweb_example_data/example_regenie.tar.gz
   tar -xzvf example_regenie.tar.gz
   ```

## 4. Prepare the configuration file 

   You can do that by copying the `../config.py` file and save it as `config.py` to your machine.

   **The `config.py` contains default settings to run the API. If you just want to test the functionality, please don't change anything.** 
   
   For anything questions related to the configurations setting, you are very welcome to contact us.

## 5. Prepare the data-preprocessing list file (if you want to preprocess your association testing data) 

    For testing, You can copy the `../manifest-example.csv` and save it as `manifest-example.csv` to your machine.

   For one's own study, please prepare your manifest csv file in a similar manner.

## 6. Ingesting (preprocessing) your data to PheWeb 2 (it can take some time)

> [!IMPORTANT]
> Important things to know before copying the code: 
> 1. `config.py` must be projected to `/app/` in the container
> 2. `/PATH/TO/YOUR/PHEWEB2/DATA/DIR` must exist (could be empty). This path must match the `PHEWEB_DATA_DIR` in `config.py`. If you are using the default setting, project `/PATH/TO/YOUR/PHEWEB2/DATA/DIR` to `/app/generated-by-pheweb/` using
>```
>--bind /PATH/TO/YOUR/PHEWEB2/DATA/DIR/:/app/generated-by-pheweb
>```
>3. If you specify you association data path (i.e. `/PATH/TO/YOUR/GWAS/DATA/DIR/`), make sure this path match the `assoc_files` column in your manifest csv file. If you are using the example data we provided, project `/PATH/TO/YOUR/GWAS/DATA/DIR/` to `/app/example_regenie/` using
>```
>--bind /PATH/TO/YOUR/GWAS/DATA/DIR/example_regenie:/app/example_regenie:ro
>```


### 6.1. Import the example manifest file describing phenotypes (**must be done first!**):
   ```
   apptainer exec --pwd /app \
   --env PYTHONPATH=/app \
   --containall --no-home \
   --bind /PATH/TO/YOUR/CONFIG/config.py:/app/config.py:ro \ # config.py must be projected to /app/
   --bind /PATH/TO/YOUR/PHEWEB2/DATA/DIR/:/PATH/TO/YOUR/PHEWEB2/DATA/DIR/ \ #could be empty, but must exist, 
   --bind /PATH/TO/YOUR/GWAS/DATA/DIR/:/PATH/TO/YOUR/GWAS/DATA/DIR/:ro \
   --bind /PATH/TO/YOUR/LIST/FILE/manifest.csv:/PATH/TO/YOUR/LIST/FILE/manifest.csv:ro \
   pheweb2-api-latest.sif \
   pheweb2 phenolist import-phenolist /PATH/TO/YOUR/LIST/FILE/manifest.csv
   ```

### 6.2. Prepross data:
   
   ```
   apptainer exec --pwd /app \
   --env PYTHONPATH=/app \
   --containall --no-home \
   --bind /PATH/TO/YOUR/CONFIG/config.py:/app/config.py:ro \ # config.py must be projected to /app/
   --bind /PATH/TO/YOUR/PHEWEB2/DATA/DIR/:/PATH/TO/YOUR/PHEWEB2/DATA/DIR/ \ #could be empty, but must exist
   --bind /PATH/TO/YOUR/GWAS/DATA/DIR/:/PATH/TO/YOUR/GWAS/DATA/DIR/:ro \
   pheweb2-api-latest.sif \
   pheweb2 process
   ```

## 7. Run automated tests of the API routes:
   ```
   apptainer exec --pwd /app \
   --env PYTHONPATH=/app \
   --containall --no-home \
   --bind /PATH/TO/YOUR/CONFIG/config.py:/app/config.py:ro \
   --bind /PATH/TO/YOUR/PHEWEB2/DATA/DIR/:/PATH/TO/YOUR/PHEWEB2/DATA/DIR/ \
   pheweb2-api-latest.sif \
   pytest tests/test_routes.py -s -v
   ```

## 8. Launch PheWeb2 API endpoint which will be available at `http://127.0.0.1:9543`:
   ```
   apptainer exec --pwd /app \
   --env PYTHONPATH=/app \
   --containall --no-home \
   --bind /PATH/TO/YOUR/CONFIG/config.py:/app/config.py:ro \
   --bind /PATH/TO/YOUR/PHEWEB2/DATA/DIR/:/PATH/TO/YOUR/PHEWEB2/DATA/DIR/ \
   pheweb2-api-latest.sif \
   pheweb2 serve --host 127.0.0.1 --port 9543
   ```

## 9. To run the PheWeb2 API in production mode:
   ```
   apptainer exec --pwd /app \
   --env PYTHONPATH=/app \
   --containall --no-home \
   --bind /PATH/TO/YOUR/CONFIG/config.py:/app/config.py:ro \
   --bind /PATH/TO/YOUR/PHEWEB2/DATA/DIR/:/PATH/TO/YOUR/PHEWEB2/DATA/DIR/ \
   pheweb2-api-latest.sif \
   pheweb2 serve --gunicorn --enable-cache
   ```