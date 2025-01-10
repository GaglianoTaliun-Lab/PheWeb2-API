from flask import current_app, send_from_directory, send_file, Response, request
import polars as pl

def getDownloadFunction(dir, phenocode, filtering_options, suffix=None):
    
    filename = phenocode
    
    if suffix is not None:
        filename += suffix
    
    headers = {
        'Content-Type': 'text/plain',
        'Transfer-Encoding': 'chunked',
    }
    # no filtering has been applied
    if filtering_options['indel'] == 'both' and filtering_options['min_maf'] == 0.0 and filtering_options['max_maf'] == 0.5:
        return Response(getUnfilteredFunction(dir, phenocode, suffix), headers = headers)
        
    # if filtering has been applied, this gets far more complicated
    # as we need to send a modified file that has been filtered.
    return Response(getFilteredFunction(dir, phenocode, filtering_options, suffix), headers = headers)
   
def getFilteredFunction(dir, phenocode, filtering_options, suffix):
        
    if not suffix:
        
        # TODO: this is mostly a repeat from utils.py... maybe I can avoid being repetitive here
        df = pl.read_csv(
            dir["PHENO_GZ_DIR"] + f"/{phenocode}.gz",
            separator = "\t",
            dtypes={
                "chrom": str,
                "pos": int,
                "ref": str,
                "alt": str,
                "rsids": str,
                "nearest_genes": str,
                "pval": float,
                "beta": float,
                "sebeta": float,
                "af": float,
            }
            )
        
        # make sure it's MAF
        df = df.with_columns(
            pl.when(pl.col("af") > 0.5)
            .then(1 - pl.col("af"))
            .otherwise(pl.col("af"))
            .alias("maf")
        )

        # filter variants that don't meet to maf requirements
        if filtering_options['indel'] == "both":
            subset = df.filter(
                pl.col("maf") > filtering_options['min_maf'],
                pl.col("maf") < filtering_options['max_maf'],
            )
        elif filtering_options['indel'] == "true":
            subset = df.filter(
                pl.col("maf") > filtering_options['min_maf'],
                pl.col("maf") < filtering_options['max_maf'],
                (
                    (pl.col("ref").str.len_bytes() != 1)
                    | (pl.col("alt").str.len_bytes() != 1)
                ),  # New condition
            )
        elif filtering_options['indel'] == "false":
            subset = df.filter(
                pl.col("maf") > filtering_options['min_maf'],
                pl.col("maf") < filtering_options['max_maf'],
                pl.col("ref").str.len_bytes() == 1,
                pl.col("alt").str.len_bytes() == 1,
            )
            
        yield "\t".join(subset.columns) + "\n"  # Header row
        for row in subset.iter_rows(named=False): # TODO: Can I do more than 1 row at a time to be faster?
            yield "\t".join(map(str, row)) + "\n"
        
    if "interaction-" in suffix:
        
        df = pl.read_csv(
            dir["INTERACTION_DIR"] + f"/{phenocode}{suffix}.gz",
            separator = "\t",
            dtypes={
                "chrom": str,
                "pos": int,
                "ref": str,
                "alt": str,
                "rsids": str,
                "nearest_genes": str,
                "pval": float,
                "beta": float,
                "sebeta": float,
                "af": float,
            }
            )
        
        # make sure it's MAF
        df = df.with_columns(
            pl.when(pl.col("af") > 0.5)
            .then(1 - pl.col("af"))
            .otherwise(pl.col("af"))
            .alias("maf")
        )

        # filter variants that don't meet to maf requirements
        if filtering_options['indel'] == "both":
            subset = df.filter(
                pl.col("maf") > filtering_options['min_maf'],
                pl.col("maf") < filtering_options['max_maf'],
            )
        elif filtering_options['indel'] == "true":
            subset = df.filter(
                pl.col("maf") > filtering_options['min_maf'],
                pl.col("maf") < filtering_options['max_maf'],
                (
                    (pl.col("ref").str.len_bytes() != 1)
                    | (pl.col("alt").str.len_bytes() != 1)
                ),  # New condition
            )
        elif filtering_options['indel'] == "false":
            subset = df.filter(
                pl.col("maf") > filtering_options['min_maf'],
                pl.col("maf") < filtering_options['max_maf'],
                pl.col("ref").str.len_bytes() == 1,
                pl.col("alt").str.len_bytes() == 1,
            )
            
        yield "\t".join(subset.columns) + "\n"  # Header row
        for row in subset.iter_rows(named=False): # TODO: Can I do more than 1 row at a time to be faster?
            yield "\t".join(map(str, row)) + "\n"

    df = pl.read_csv(dir["PHENO_GZ_DIR"] + f"/{phenocode}{suffix}.gz",
                    separator = "\t",
                    dtypes={
                        "chrom": str,
                        "pos": int,
                        "ref": str,
                        "alt": str,
                        "rsids": str,
                        "nearest_genes": str,
                        "pval": float,
                        "beta": float,
                        "sebeta": float,
                        "af": float,
                    }
            )
    
    # make sure it's MAF
    df = df.with_columns(
        pl.when(pl.col("af") > 0.5)
        .then(1 - pl.col("af"))
        .otherwise(pl.col("af"))
        .alias("maf")
    )

    # filter variants that don't meet to maf requirements
    if filtering_options['indel'] == "both":
        subset = df.filter(
            pl.col("maf") > filtering_options['min_maf'],
            pl.col("maf") < filtering_options['max_maf'],
        )
    elif filtering_options['indel'] == "true":
        subset = df.filter(
            pl.col("maf") > filtering_options['min_maf'],
            pl.col("maf") < filtering_options['max_maf'],
            (
                (pl.col("ref").str.len_bytes() != 1)
                | (pl.col("alt").str.len_bytes() != 1)
            ),  # New condition
        )
    elif filtering_options['indel'] == "false":
        subset = df.filter(
            pl.col("maf") > filtering_options['min_maf'],
            pl.col("maf") < filtering_options['max_maf'],
            pl.col("ref").str.len_bytes() == 1,
            pl.col("alt").str.len_bytes() == 1,
        )
        
    print("starting to yield filtered...")
    print("\t".join(subset.columns) + "\n")
    yield "\t".join(subset.columns) + "\n"  # Header row
    for row in subset.iter_rows(named=False): # TODO: Can I do more than 1 row at a time to be faster?
        print("\t".join(map(str, row)) + "\n")
        yield "\t".join(map(str, row)) + "\n"
    
def getUnfilteredFunction(dir, phenocode, suffix):
    
    print("getUnfilteredFunction called")
    if not suffix:
        # TODO: this is mostly a repeat from utils.py... maybe I can avoid being repetitive here
        df = pl.read_csv(
            dir["PHENO_GZ_DIR"] + f"/{phenocode}.gz",
            separator = "\t",
            dtypes={
                "chrom": str,
                "pos": int,
                "ref": str,
                "alt": str,
                "rsids": str,
                "nearest_genes": str,
                "pval": float,
                "beta": float,
                "sebeta": float,
                "af": float,
            }
            )
    
        # make sure it's MAF
        df = df.with_columns(
            pl.when(pl.col("af") > 0.5)
            .then(1 - pl.col("af"))
            .otherwise(pl.col("af"))
            .alias("maf")
        )
            
        yield "\t".join(df.columns) + "\n"  # Header row
        for row in df.iter_rows(named=False): # TODO: Can I do more than 1 row at a time to be faster?
            yield "\t".join(map(str, row)) + "\n"
        
    if "interaction-" in suffix:
        
        df = pl.read_csv(
            dir["INTERACTION_DIR"] + f"/{phenocode}{suffix}.gz",
            separator = "\t",
            dtypes={
                "chrom": str,
                "pos": int,
                "ref": str,
                "alt": str,
                "rsids": str,
                "nearest_genes": str,
                "pval": float,
                "beta": float,
                "sebeta": float,
                "af": float,
            }
            )
            
        # make sure it's MAF
        df = df.with_columns(
            pl.when(pl.col("af") > 0.5)
            .then(1 - pl.col("af"))
            .otherwise(pl.col("af"))
            .alias("maf")
        )
        
        yield "\t".join(df.columns) + "\n"  # Header row
        for row in df.iter_rows(named=False): # TODO: Can I do more than 1 row at a time to be faster?
            yield "\t".join(map(str, row)) + "\n"

    # else : ...
    df = pl.read_csv(dir["PHENO_GZ_DIR"] + f"/{phenocode}{suffix}.gz",
                    separator = "\t",
                    dtypes={
                        "chrom": str,
                        "pos": int,
                        "ref": str,
                        "alt": str,
                        "rsids": str,
                        "nearest_genes": str,
                        "pval": float,
                        "beta": float,
                        "sebeta": float,
                        "af": float,
                    }
            )
    # make sure it's MAF
    df = df.with_columns(
        pl.when(pl.col("af") > 0.5)
        .then(1 - pl.col("af"))
        .otherwise(pl.col("af"))
        .alias("maf")
    )
        
    print("starting to yield unfiltered...")
    print("\t".join(df.columns) + "\n")
    yield "\t".join(df.columns) + "\n"  # Header row
    for row in df.iter_rows(named=False): # TODO: Can I do more than 1 row at a time to be faster?
        print("\t".join(map(str, row)) + "\n")
        yield "\t".join(map(str, row)) + "\n"