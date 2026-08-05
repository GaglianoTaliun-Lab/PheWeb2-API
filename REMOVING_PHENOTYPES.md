# Removing data

The goal of these instructions is to remove GWAS data to an existing PheWeb 2 instance. They assume that the initial data ingestion has already been completed with a first dataset.

> [!NOTE]
> This process will remove any trace of phenotypes to remove, with the possibility to backup files.


## 1. Configuration file

You may set `ENABLE_BACKUPS` to true so that any file that is replaced will be copied to the /generated-by-pheweb/backups directory before being overwritten or deleted.


### 2. Creating the Manifest file

The Manifest file is a comma-separated (CSV) file that describes phenotypes to be removed. The [manifest-example.csv](manifest-example.csv) file serves as an example of the Manifest file, and the table below lists the required columns.

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


2. Run phenotype removal process with:

```
pheweb2 remove-phenotypes
```

Phenotypes present in `pheno-mask.json` file will be remove from generate-by-pheweb folder.