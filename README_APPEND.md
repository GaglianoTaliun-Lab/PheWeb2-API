# Ingesting new data

The goal of these instructions is to append new GWAS data to an existing PheWeb2 instance. They assume that the initial data ingestion has already been completed with a first dataset.

## 1. Test it out using our second small example dataset

To try this feature, you can download our second small example dataset by following these steps:

> [!WARNING]
> To avoid accidentally mixing example data with your own, load the example datasets into a separate PheWeb2 instance.

1. Download and unarchive the second example data (~18 GB):

   ```
   wget https://objets.juno.calculquebec.ca/swift/v1/AUTH_290e6dcc5e264b34b401f54358bd4c54/pheweb_example_data/example_regenie_2.tar.gz
   tar -xzvf example_regenie_2.tar.gz
   ```

2. Import the manifest file into PheWeb2:

   ```
   pheweb2 phenolist import-phenolist /manifest-exemple-2.csv
   ```

   This command creates a new `pheno-list.json` file in the root directory; the previous one is moved to `generated-by-pheweb/backups/`.

3. Follow the same steps as the [first-time ingest](), using the second example manifest file as input.

## 2. Configuration file

When appending new GWAS data, you should ideally use the same set of variable–value pairs that were used during the initial data ingestion.

> [!NOTE]
> It is recommended to set `ENABLE_BACKUPS` to `true`. Some files must be replaced to include the new phenotypes. When this option is enabled, any file that is replaced is copied to `generated-by-pheweb/backups/` before being overwritten. Be aware that some backup files may require a considerable amount of disk space.

> [!WARNING]
> The first example dataset uses `ADD-INT_SNPxBSEX=2` as value for the `INTERACTION_TEST_NAME` variable. Be sure to change this value to `ADD-INT_SNPxsex` for the second example dataset. No other configuration changes are needed.

## 3. Run using your own data

Your new manifest file should include the new set of phenotypes to ingest.

1. Import the manifest file into PheWeb2:

   ```
   pheweb2 phenolist import-phenolist /path/to/manifest.csv
   ```

   This command creates a new `pheno-list.json` file in the root directory; the previous one is moved to `generated-by-pheweb/backups/`.

2. Follow the same steps as the [first-time ingest](), using your new manifest file as input.

> [!NOTE]
> The new manifest file may include existing phenotypes, but this is not required. Existing phenotypes are not reprocessed. However, if the manifest file includes an existing phenotype with new stratifications, only the new stratifications are ingested. Here, "existing phenotypes" refers to phenotypes that have already been ingested. The `pheno-list.json` file used during the initial data ingestion is no longer required.
