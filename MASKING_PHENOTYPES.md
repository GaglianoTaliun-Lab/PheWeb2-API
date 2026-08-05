# Masking data

The goal of these instructions is to mask GWAS data to an existing PheWeb 2 instance. They assume that the initial data ingestion has already been completed with a first dataset.

> [!NOTE]
> Masking is different than removing. Masking will disallow masked phenotypes to be share from any endpoints. generate-by-pheweb folder will still contains masked phenotypes.


## 1. Configuration file

You can enable or disable phenotype masking in the config.py by setting the `ENABLE_MASKING` variable in SECTION D: Runtime parameters.


### 2. Creating the Manifest file

The Manifest file is a comma-separated (CSV) file that describes phenotypes to be masked. The [manifest-example.csv](manifest-example.csv) file serves as an example of the Manifest file, and the table below lists the required columns.

| column description                                  | value         | allowed values                      | required? |
| --------------------------------------------------- | ------------- | ----------------------------------- | --------- |
| Phenotype Code                                      | phenocode     | string                              | true      |
| Variable of Interaction Testing                     | interaction   | string                              | true     |
| Category of stratification (Can be more than one)   | stratification   | "stratification.*" (where *=string) | true     |



## 3. Run using your own data

1. Import the manifest file into PheWeb2:
   ```
   pheweb2 phenolist import-phenomask /path/to/manifest.csv
   ```
   This command creates a `pheno-mask.json` file in the root directory.

2. Make sure `ENABLE_MASKING` is set to True in the config.py file.

3. That's all! If you have a current instance of PheWeb2 backend running, you will need to restart it.
