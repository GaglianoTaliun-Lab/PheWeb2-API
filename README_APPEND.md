# Ingesting new data

 The goals of these instructions is to append new genome-wide and phenome-wide association studies (GWAS/PheWAS) data into an existing PheWeb2.0 instance. It implies that the first-time data ingest as been fully completed with a first dataset.

## 1. Test it out using our second small example data

To try this feature, one can download our second small exemple dataset with the following steps:

1. Download and unarchive the example data (~13 GB):
```
wget https://objets.juno.calculquebec.ca/swift/v1/AUTH_290e6dcc5e264b34b401f54358bd4c54/pheweb_example_data/example_regenie.tar.gz
tar -xzvf example_regenie.tar.gz
```

2. follow same steps used for the first-time ingest using downloaded manifest file.

## 2. Configuration file
When appending new GWAS data, you should ideally keep same set of variable-value pairs used for the first-time ingest.

> [!NOTE]
> It is recommended to set `ENABLE_BACKUPS` to true. Some files have to be replace in order to include new phenotypes. With this options set, files being replace will be moved to /generated-by-pheweb/backups folder. Be aware that some files may uses considerable amount of disk space.


## 3. Steps

You may follow same steps used for the first-time ingest!

Your manifest file should includes the new set of phenotypes to include.

> [!NOTE]
> The manifest file can includes existing phenotypes as well but it is not required. Existing phenotypes won't be reprocessed. If the manifest file contains an existing phenotype with new stratifications, these stratifications will be ingested. We are referring to existing phenotypes as phenotypes already ingested.
