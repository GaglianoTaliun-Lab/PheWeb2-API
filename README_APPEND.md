# Ingesting new data

 The goals of these instructions is to append new GWAS data into an existing PheWeb2.0 instance. It implies that the first-time data ingest as been fully completed with a first dataset.

## 1. Test it out using our second small example data

To try this feature, one can download our second small exemple dataset with the following steps:

1. Download and unarchive the second example data (~19 GB):
```
PLACE HOLDER

For now example_regenie_2 folder already included.
```

2. follow same steps used for the first-time ingest using the second example manifest file as input.

## 2. Configuration file
When appending new GWAS data, you should ideally use the same set of variable–value pairs that were used for the initial ingest.

> [!NOTE]
> It is recommended to set `ENABLE_BACKUPS` to true. Some files have to be replace in order to include new phenotypes. With this options set, files being replace will be copied/moved to /generated-by-pheweb/backups folder. Be aware that some files may uses considerable amount of disk space.

TEMP NOTE: The first example dataset uses ADD-INT_SNPxBSEX=2 as the value of the INTERACTION_TEST_NAME variable. Be sure to change this value to ADD-INT_SNPxsex for the second example dataset. No need to change other configs

(Personally, I would replace the first example dataset instead.)


## 3. Run using your own data

Your new manifest file should includes the new set of phenotypes to include.

You may follow the same steps described for the first-time ingest!

> [!NOTE]
> The new manifest file can includes existing phenotypes as well but it is not required. Existing phenotypes won't be reprocessed. If the manifest file contains an existing phenotype with new stratifications, these stratifications will be ingested. We are referring to existing phenotypes as phenotypes already ingested. The previous pheno-list.json file used for the first-time ingest is no longer needed and will be backup by default.
