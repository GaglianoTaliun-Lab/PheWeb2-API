# PheWeb2 API
[![Docker Pulls](https://img.shields.io/docker/pulls/xiaoh11/pheweb2-api)](https://hub.docker.com/r/xiaoh11/pheweb2-api)
[![Docker Image Version (latest by date)](https://img.shields.io/docker/v/xiaoh11/pheweb2-api?sort=semver)](https://hub.docker.com/r/xiaoh11/pheweb2-api)


**Please cite our preprint:** 

Bellavance, J., Xiao, H., Chang, L., Kazemi, M., Wickramasinghe, S., Mayhew, A.J., Raina, P., VandeHaar, P., Taliun, D., & Gagliano Taliun, S.A. (2025). Exploring and visualizing stratified genome-wide association study results with PheWeb 2. https://doi.org/10.21203/rs.3.rs-7463215/v1

This is an implementation of the data model and API for [PheWeb2](https://github.com/GaglianoTaliun-Lab/PheWeb2/tree/main) — an enhanced version of the original [PheWeb](https://github.com/statgen/pheweb) web-based tool for interactive querying, visualizing, and sharing summary-level results from genome-wide and phenome-wide association studies (GWAS/PheWAS), which offers intuitive and efficient support for stratified analysis results. PheWeb2 decouples the data model and API from the user interface (UI) to improve code maintenance and reusability and allow results querying by other external resources and applications.

> [!TIP]
> If you've already set up the PheWeb2 API, you can proceed to install and launch the [PheWeb2](https://github.com/GaglianoTaliun-Lab/PheWeb2) user interface.

> [!NOTE]
> We provide a containerized setup (using Docker image) for easy deployment and reliable version management. Please check the [detailed documentation](./apptainer/README.md).

## 1. Install

> [!NOTE]
> The code was developed and tested with Python 3.12+ on Linux-based OS.

You can install PheWeb2 and all required dependencies within a virtual environment using the following steps:
1. Clone this repository:
   ```
   git clone https://github.com/GaglianoTaliun-Lab/PheWeb2-API.git
   cd PheWeb2-API
   ```
2. Create and activate Python virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install PheWeb2 Python package and its dependencies:
   ```
   pip install -e .
   ```

<details>
   <summary>
      Click to see another installing option through apptainer
   </summary>
   
   ```
   mkdir -p PheWeb2-API
   cd PheWeb2-API
   apptainer pull pheweb2-api-latest.sif docker://xiaoh11/pheweb2-api:latest
   ```
   If you prefer to build the apptainer image based on a def file, we also provided it in [`pheweb2api.def`](./apptainer/pheweb2api.def)

   You can copy this file to your machine and do
   ```
   mkdir -p PheWeb2-API
   cd PheWeb2-API
   apptainer build pheweb2-api-latest.sif PATH/TO/YOUR/pheweb2api.def
   ```

   For detailed information, please head to [documentation of implementing PheWeb2 in container](./apptainer/README.md#2-build-the-apptainer-image)
</details>

## 2. Test it out using our small example data
To familiarize yourself with PheWeb2, we recommend first trying to configure and run it with the provided example dataset by following the steps below.

> [!IMPORTANT]
>Please note that the `config.py` contains default settings run the API. For testing/getting familiar with the functionality, please don't change anything. <br/>
>For example, we provided the reference files (gene aliases files, genes bed files, and rsid files) from our web server bucket with default setting
>```
>HG_BUILD_NUMBER = 38
>DBSNP_VERSION = 157
>GENCODE_VERSION = 48
>```
>if you need any other versions for your data, a hint will pop up during `pheweb2 process` like<br/>
>```
>Failed to download genes from our bucket
>Try `pheweb2 download-genes-from-scratch` instead
>```
> Then, please manually download them during using commands:
>```
>pheweb2 download-genes-from-scratch
>pheweb2 download-rsids-from-scratch
>```

1. Download and unarchive the example data (~13 GB):
   ```
   wget https://objets.juno.calculquebec.ca/swift/v1/AUTH_290e6dcc5e264b34b401f54358bd4c54/pheweb_example_data/example_regenie.tar.gz
   tar -xzvf example_regenie.tar.gz
   ```
2. Import the example manifest file describing phenotypes:
   ```
   pheweb2 phenolist import-phenolist manifest-example.csv
   ```
   <details>
      <summary>
         Click to see another option through apptainer
      </summary>

      If you download everything in `PheWeb2-API`
      
      ```
      mkdir -p generated-by-pheweb

      apptainer exec --pwd /app \
      --env PYTHONPATH=/app \
      --containall --no-home \
      --bind ./config.py:/app/config.py:ro \
      --bind ./generated-by-pheweb:/app/generated-by-pheweb \ #could be empty, but must exist
      --bind ./example_regenie:/app/example_regenie:ro \
      --bind ./manifest-example.csv:/app/manifest-example.csv:ro \
      pheweb2-api-latest.sif \
      pheweb2 phenolist import-phenolist manifest-example.csv
      ```

      For detailed information, please head to [documentation of implementing PheWeb2 in container](./apptainer/README.md#61-import-the-example-manifest-file-describing-phenotypes-must-be-done-first)
   </details>
3. Ingest the example data into PheWeb2 (this can take some time):
   ```
   pheweb2 process
   ```
   <details>
      <summary>
         Click to see another option through apptainer
      </summary>

      If you download everything in `PheWeb2-API`
      
      ```
      apptainer exec --pwd /app \
      --env PYTHONPATH=/app \
      --containall --no-home \
      --bind ./config.py:/app/config.py:ro \
      --bind ./generated-by-pheweb:/app/generated-by-pheweb \ #could be empty, but must exist
      --bind ./example_regenie:/app/example_regenie:ro \
      pheweb2-api-latest.sif \
      pheweb2 process
      ```

      For detailed information, please head to [documentation of implementing PheWeb2 in container](./apptainer/README.md#62-prepross-data)
   </details>

4. Run automated tests of the API routes:
   ```
   pytest tests/test_routes.py -s -v
   ```
   <details>
      <summary>
         Click to see another option through apptainer
      </summary>
      
      ```
      apptainer exec --pwd /app \
      --env PYTHONPATH=/app \
      --containall --no-home \
      --bind ./config.py:/app/config.py:ro \
      --bind ./generated-by-pheweb:/app/generated-by-pheweb \
      pheweb2-api-latest.sif \
      pytest tests/test_routes.py -s -v
      ```

      For detailed information, please head to [documentation of implementing PheWeb2 in container](./apptainer/README.md#7-run-automated-tests-of-the-api-routes)
   </details>
   <details>
     <summary>Click to see an example of passed tests.</summary>
     
     ```
     tests/test_routes.py::test_get_phenotypes                PASSED
     tests/test_routes.py::test_get_gene_names                PASSED
     tests/test_routes.py::test_get_gene_PCSK9                PASSED
     tests/test_routes.py::test_get_tophits                   PASSED
     tests/test_routes.py::test_get_stratifications           PASSED
     tests/test_routes.py::test_get_variant_10_112999020_G_T  PASSED
     ```
   </details>

5. Launch PheWeb2 API endpoint which will be available at `http://127.0.0.1:9543`:
   ```
   pheweb2 serve --host 127.0.0.1 --port 9543
   ```
   <details>
      <summary>
         Click to see another option through apptainer
      </summary>
      
      ```
      apptainer exec --pwd /app \
      --env PYTHONPATH=/app \
      --containall --no-home \
      --bind ./config.py:/app/config.py:ro \
      --bind ./generated-by-pheweb:/app/generated-by-pheweb \
      pheweb2-api-latest.sif \
      pheweb2 serve --host 127.0.0.1 --port 9543
      ```

      For detailed information, please head to [documentation of implementing PheWeb2 in container](./apptainer/README.md#8-launch-pheweb2-api-endpoint-which-will-be-available-at-http1270019543)
   </details>

6. To access the interactive API documentation, open your internet browser and navigate to `http://localhost:9543/docs`, assuming you are running it on the same machine at port 9543.


## 3. Run using your own data

### 3.1. Configuration file
The self-documenting [config.py](config.py) configuration file includes all the variables that determine where PheWeb 2 API stores ingested GWAS data, how it processes this data, and how it serves it through HTTP. 

When performing GWAS data ingestion, you should focus on adjusting the variables in *SECTION A*, *SECTION B*, and *SECTION C* of this file:

- *SECTION A* of the [config.py](config.py) file lists the configuration variables that control the location of the processed GWAS summary statistics.
- *SECTION B* of the [config.py](config.py) file lists the configuration variables that control the versions of the external public databases such as dbSNP and GENCODE.
- *SECTION C* of the [config.py](config.py) file lists the configuration variables that control GWAS summary statistics ingestion.

When running an API endpoint, you should focus on adjusting the variables in *SECTION D* of the [config.py](config.py) file that control the API URL address, the number of API workers to handle HTTP requests, and so on.

### 3.2. Minimal GWAS summary statistics file

> [!NOTE]
> The current version of PheWeb 2 API has been tested using GWAS summary statistics output files generated by [Regenie](https://rgcgithub.github.io/regenie/).

> [!IMPORTANT]
> PheWeb 2 relies on the `TEST`/`test` column in GWAS summary statistics files to distinguish variant effects from interactions. While Regenie and [PLINK2](https://www.cog-genomics.org/plink/2.0/) GWAS ummary statistics files by default include the `TEST` column, which provides details on the statistical tests reported (e.g., *ADD*, *ADD-CONDTL*, *ADD-INT_SNPxVAR*, *ADDxCOVAR1*), other tools may not include this column. In such cases, we recommend adding a `TEST` column with the appropriate values to your GWAS ummary statistics files. Then, you can define the values representing each test in your GWAS ummary statistics files using `ASSOC_TEST_NAME` and `INTERACTION_TEST_NAME` variables in the [config.py](config.py) file.

The table below presents a minimal list of expected columns in GWAS summary statistics files. You can modify their names using the `FIELD_ALIASES` variable in the [config.py](config.py) file.

| column description | column name | allowed values              |
| ------------------ | ----------- | --------------------------- |
| Chromosome         | CHROM       | 1-22, 23/X                  |
| Position           | GENPOS      | Integer                     |
| Reference Allele   | ALLELE0     | Must match reference genome |
| Effect Allele      | ALLELE1     | Anything                    |
| Beta               | BETA        | Float                       |
| Standard Error     | SE          | Float                       |
| Log-10 P-value     | LOG10P      | Float                       |
| Statistical Test   | TEST        | Anything. Typical values: ADD, ADD-CONDTL, ADD-INT_SNPxVAR, ... |

### 3.3. Summary statistics exclusion criteria
During the ingestion of GWAS summary statistics, PheWeb 2 will apply the following exclusions:
- If a required field is null (i.e., any of the following: [’’, ‘.’, ‘NA’, ‘N/A’, ‘n/a’, ‘nan’, ‘-nan’, ‘NaN’, ‘-NaN’, ‘null’, ‘NULL’]), the variant will be discarded.
- If the minor allele frequency (MAF) of the variant falls below a specified threshold (defined by the `ASSOC_MIN_MAF` variable in the [config.py](config.py) file), the variant will be excluded.
- If the MAF of the variant is below a specified threshold (defined by the `INTERACTION_MIN_MAF` variable in the [config.py](config.py) file), the interaction effect for this variant will not be imported.
- When genotype imputation quality scores are available, if the imputation quality for a variant falls below a specified threshold (defined by the `MIN_IMP_QUALITY` variable in the [config.py](config.py) file), the variant will be excluded.
  
> [!NOTE]
> When filtering by imputation quality scores, the scores can be provided as a column inside the GWAS summary statistics file (e.g., the Regenie outputs imputation quality scores in the `INFO` column) or in the external indexed VCF files outputted by the genotype imputation software (e.g., [minimac4](https://github.com/statgen/Minimac4)). See an example inside the [config.py](config.py) file.

> [!IMPORTANT]
> The imputation quality scores recomputed by Regenie may differ from the scores outputted by the genotype imputation software, as Regenie uses dosages only for a subset of individuals included in GWAS who have phenotype and covariate data. When conducting stratified analyses, we recommend using the original genotype imputation quality scores computed by the imputation software.

### 3.4. Creating the Manifest file

To ingest GWAS summary statistics files into PheWeb2, you need to create the Manifest file. The Manifest file is a comma-separated (CSV) file that describes each GWAS summary statistics file you have. The [manifest-example.csv](manifest-example.csv) file serves as an example of the Manifest file, and the table below lists the required and optional columns.

| column description                                  | value         | allowed values                      | required? |
| --------------------------------------------------- | ------------- | ----------------------------------- | --------- |
| Phenotype Code                                      | phenocode     | string                              | true      |
| Phenotype Description                               | phenostring   | string                              | true      |
| Location of summary statistics                      | assoc_files   | string                              | true      |
| Number of tested samples / participants             | num_samples   | int                                 | true     |
| Number of tested cases                              | num_cases     | int                                 | false     |
| Number of tested controls                           | num_controls  | int                                 | false     |
| Category of trait                                   | category      | float                               | false     |
| Variable of Interaction Testing                     | interaction   | string                              | false     |
| Category of stratification (Can be more than one)   | interaction   | "stratification.*" (where *=string) | false     |


### 3.5a. Ingesting GWAS summary statistics files using a single node

> [!NOTE]
> Although parallelized, data ingestion may still take some time, depending on the number and size of your GWAS summary statistics files.
> The ingested data will be by default stored inside the `generated_by_pheweb` folder, but this can be controlled using the `PHEWEB_DATA_DIR` variable inside the [config.py](config.py) file.
> After the data ingestion, you may archive your original GWAS summary statistics files, as PheWeb2 will no longer need them.

Once you have edited the [config.py](config.py) file and created the Manifest file, execute the following commands inside the root directory of the PheWeb2 API.

1. Import the manifest file into PheWeb2:
   ```
   pheweb2 phenolist import-phenolist /path/to/manifest.csv
   ```
   This command creates a `pheno-list.json` file in the root directory.

2. Set the number of parallel ingestion jobs using the `NUM_PROCS` parameter in the [config.py](config.py) file.

3. Ingest the GWAS summary statistics into PheWeb2:
   ```
   pheweb2 process
   ```

### 3.5b. Ingesting GWAS summary statistics files using SLURM or SGE

> [!NOTE]
> Although parallelized, data ingestion may still take some time, depending on the number and size of your GWAS summary statistics files.
> The ingested data will be by default stored inside the `generated_by_pheweb` folder, but this can be controlled using the `PHEWEB_DATA_DIR` variable inside the [config.py](config.py) file.
> After the data ingestion, you may archive your original GWAS summary statistics files, as PheWeb2 will no longer need them.


Once you have edited the [config.py](config.py) file and created the Manifest file, execute the following commands inside the root directory of the PheWeb2 API.

1. Import the manifest file into PheWeb2:
   ```
   pheweb2 phenolist import-phenolist /path/to/manifest.csv
   ```
   This command creates a `pheno-list.json` file in the root directory.

2. Create a SLURM/SGE job submission bash script for parsing the GWAS summary statistics files:
   ```
   pheweb2 cluster --engine=slurm --step=parse --N_per_job=3
   ```
   or
   ```
   pheweb2 cluster --engine=sge --step=parse --N_per_job=3
   ```
   A bash script named `slurm-parse-[DATETIME].sh` or `sge-parse-[DATETIME].sh` will be generated in the `generated-by-pheweb/tmp/` directory. If you have modified the `PHEWEB_DATA_DIR` variable in the [config.py](config.py) configuration file, the script will be placed in the `[PHEWEB_DATA_DIR]/tmp/` directory instead.

   To specify the maximum number of GWAS files to parse sequentially per parallel job, use the `--N_per_job` option (the default is 3). You can also include an optional `--account `argument in the `pheweb2 cluster` command to specify your SLURM account name if needed.

3. Submit the SLURM/SGE jobs for parsing GWAS summary statistics files to the queue:
   ```
   sbatch generated-by-pheweb/tmp/slurm-parse-[DATETIME].sh
   ```
   or
   ```
   sge generated-by-pheweb/tmp/sge-parse-[DATETIME].sh
   ```
   
> [!IMPORTANT]
> Depending on your GWAS files' size and your cluster's configuration, you may need to adjust the job submission parameters in the bash script. This could involve increasing the job time limit or memory limit, or specifying a queue/account name.

4. After all SLURM/SGE jobs submitted to the queue have successfully finished running, you can proceed to the next step. This involves generating a union of all genetic variants from the GWAS summary statistics files. Note that this step does not utilize SLURM/SGE; instead, it employs local parallelization, which is controlled by the `NUM_PROCS` variable in the [config.py](config.py) configuration file.
   ```
   pheweb2 sites
   ```
   This creates the `generated-by-pheweb/sites/sites-unannotated.tsv` file.

5. Next, download the gene aliases database (internet access is required):
   ```
   pheweb2 make-gene-aliases-sqlite3
   ```

6. Download the rsID database and annotate it with gene names in the sites file (this may take a few hours; internet access is required):
   ```
   pheweb2 add-rsids
   pheweb2 add-genes
   ```

7. Create a mapping between GWAS variants and rsIDs:
   ```
   pheweb2 make-cpras-rsids-sqlite3
   ```

8. The upcoming processing steps will again utilize SLURM/SGE for parallelization, similar to steps 2-3. Please create bash scripts for SLURM/SGE to augment variant-phenotype data and generate Manhattan and QQ plots:
   ```
   pheweb2 cluster --engine=slurm --step=augment-phenos --N_per_job=3
   pheweb2 cluster --engine=slurm --step=manhattan --N_per_job=3
   pheweb2 cluster --engine=slurm --step=qq --N_per_job=3
   ```
   or
   ```
   pheweb2 cluster --engine=sge --step=augment-phenos --N_per_job=3
   pheweb2 cluster --engine=sge --step=manhattan --N_per_job=3
   pheweb2 cluster --engine=sge --step=qq --N_per_job=3
   ```

   After generating the job submission bash scripts, you can submit your jobs to the SLURM or SGE queue, just as you did in step 3.
   ```
   sbatch generated-by-pheweb/tmp/slurm-augment-phenos-[DATETIME].sh
   sbatch generated-by-pheweb/tmp/slurm-manhattan-[DATETIME].sh
   sbatch generated-by-pheweb/tmp/slurm-qq-[DATETIME].sh
   ```
   or
   ```
   sge generated-by-pheweb/tmp/sge-augment-phenos-[DATETIME].sh
   sge generated-by-pheweb/tmp/sge-manhattan-[DATETIME].sh
   sge generated-by-pheweb/tmp/sge-qq-[DATETIME].sh
   ``` 

9. Once all SLURM/SGE jobs from the previous step have successfully completed, proceed to create the phenotype matrix:
    ```
    pheweb2 matrix
    ```

10. Then, create the database to map each gene to phenotypes:
    ```
    pheweb2 gather-pvalues-for-each-gene
    ```

11. Then, prepare a list of all phenotypes and all statistically significant results:
    ```
    pheweb2 phenotypes
    pheweb2 top-hits
    ```

12. Generate a list of phenotypes with the statistically significant associations:
    ```
    pheweb2 best-of-pheno
    ```

13. Generate a database for quick lookups of variants, genes, and phenotypes using incomplete names. This will support the functionality of the search boxes effectively.
    ```
    pheweb2 generate-autocomplete-db
    ```

14. Run this command to validate the process and ensure that all expected files were generated.
    ```
    pheweb2 process
    ``` 

### 3.6a. Running API server in development mode
1. Adjust the configuration variables in *SECTION D* of the configuration file located at [config.py](config.py). Among other things, you may want to enable debug mode by setting the `ENABLE_DEBUG` variable.

2. To run the API in development mode, run:
   ```
   pheweb2 serve
   ```
   <details>
     <summary>Click to see an example of terminal output in the development mode.</summary>
     
     ```
     * Serving Flask app 'pheweb_api.api_app'
     * Debug mode: on
     WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
     * Debugger is active!
     ```
   </details>

3. To test the API once it is running, execute the following commands in a different terminal on the same machine. If necessary, change the port number from 9543.
   ```
   curl -X GET "http://localhost:9543/phenotypes/"
   curl -X GET "http://localhost:9543/gene/"
   curl -X GET "http://localhost:9543/phenotypes/tophits"
   curl -X GET "http://localhost:9543/variant/stratification_list"
   ```
   You should see the messages in the terminal that run the API, prefixed with `[DEBUG]`.

5. To access the interactive API documentation and test API queries, open your internet browser and go to `http://localhost:9543/`, provided you are running it on the same machine at port 9543. If you are using a different host or port, please update the HTTP address in your browser to match the settings in the [config.py](config.py) configuration file.

### 3.6b. Running API server in production mode
1. Adjust the configuration variables in *SECTION D* of the configuration file located at [config.py](config.py). Make sure to disable debug mode by setting the `ENABLE_DEBUG` variable to `False`.

> [!NOTE]
> If you plan to run the API behind a reverse proxy, such as Apache or Nginx, and want all API routes to start with a specific prefix (like `/api` or `/api/v1`), you should set the `API_URL_PREFIX` variable in the [config.py](config.py) configuration file.

> [!WARNING]
> If you need to allow access to API only from a specific machine, then set the `CORS_ORIGINS` variable in the [config.py](config.py) configuration file.

2. To run the API server in production mode, run:
   ```
   pheweb2 serve --gunicorn --enable-cache
   ```

3. Once the API is running, you can test it by executing the following commands on the same machine. Change the 9543 port number if required.
   ```
   curl -X GET "http://localhost:9543/phenotypes/"
   curl -X GET "http://localhost:9543/gene/"
   curl -X GET "http://localhost:9543/phenotypes/tophits"
   curl -X GET "http://localhost:9543/variant/stratification_list"
   ```

4. To access the interactive API documentation, open your internet browser and navigate to `http://localhost:9543/`, assuming you are running it on the same machine at port 9543. If not, you will need to modify the HTTP address in your browser to match the host and port specified in the [config.py](config.py) configuration file.

