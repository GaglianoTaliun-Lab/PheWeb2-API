from flask import current_app, send_from_directory, send_file, Response, request
import polars as pl
from ..conf import get_pheweb_data_dir
import os

def getDownloadFunction(phenocode, filtering_options, suffix=None):
    
    filename = phenocode
    
    if suffix is not None:
        filename += suffix
    
    headers = {
        'Content-Type': 'text/plain',
        'Transfer-Encoding': 'chunked',
    }
    # no filtering has been applied
    if filtering_options['indel'] == 'both' and filtering_options['min_maf'] == 0.0 and filtering_options['max_maf'] == 0.5:
        headers["Content-Disposition"] = f'attachment; filename={filename}.txt'

        return Response(getUnfilteredFunction(phenocode, suffix), headers = headers)
        
    # if filtering has been applied, this gets far more complicated
    # as we need to send a modified file that has been filtered.
    headers["Content-Disposition"] = f'attachment; filename=filtered-{filename}.txt'
    return Response(getFilteredFunction(phenocode, filtering_options, suffix), headers = headers)
   

def getFilteredFunction(phenocode, filtering_options, suffix):
    
    column_dtypes = {
        0: str,   # chrom
        1: int,   # pos
        2: str,   # ref
        3: str,   # alt
        4: str,   # rsids
        5: str,   # nearest_genes
        6: str,   # test
        7: float, # pval
        8: float, # beta
        9: float, # sebeta
        10: float, # af
        11: float, # imp_quality
        12: int, # n_samples
    }

    def process_and_filter_chunk(chunk, header):
        # Ensure MAF
        af_index = header.index('af')
        ref_index = header.index('ref')
        alt_index = header.index('alt')
        
        maf_col = pl.when(pl.nth(af_index) > 0.5).then(1 - pl.nth(af_index)).otherwise(pl.nth(af_index)).alias("maf")
        
        chunk = chunk.with_columns(maf_col)

        # Apply filtering options
        if filtering_options['indel'] == "both":
            filtered_chunk = chunk.filter(
                (pl.col("maf") > filtering_options['min_maf']) &
                (pl.col("maf") < filtering_options['max_maf'])
            )
        elif filtering_options['indel'] == "true":
            filtered_chunk = chunk.filter(
                (pl.col("maf") > filtering_options['min_maf']) &
                (pl.col("maf") < filtering_options['max_maf']) &
                (
                    (pl.nth(ref_index).str.len_bytes() != 1) |
                    (pl.nth(alt_index).str.len_bytes() != 1)
                )
            )
        elif filtering_options['indel'] == "false":
            filtered_chunk = chunk.filter(
                (pl.col("maf") > filtering_options['min_maf']) &
                (pl.col("maf") < filtering_options['max_maf']) &
                (pl.nth(ref_index).str.len_bytes() == 1) &
                (pl.nth(alt_index).str.len_bytes() == 1)
            )
        else:
            filtered_chunk = chunk  # No filtering applied
        return filtered_chunk

    def read_in_chunks(file_path, chunk_size=1_000_000, header=None):
        total_rows = 0
                
        while True:
            chunk = pl.read_csv(
                file_path, 
                separator="\t", 
                dtypes={col_name: column_dtypes[i] for i, col_name in enumerate(header)},  # Map columns by index
                rechunk=False,
                n_rows=chunk_size,
                skip_rows=total_rows
            )

            if chunk.is_empty():
                break

            # Skip header row for all but the first chunk
            if header is not None and total_rows == 0:
                chunk = chunk[1:]
            yield chunk
            total_rows += chunk.shape[0]

    file_path = None
    if not suffix:
        file_path = os.path.join(get_pheweb_data_dir(), "pheno_gz", f"{phenocode}.gz")
    elif "interaction-" in suffix:
        file_path = os.path.join(get_pheweb_data_dir(), "interaction", f"{phenocode}{suffix}.gz")
    else:
        file_path = os.path.join(get_pheweb_data_dir(), "pheno_gz", f"{phenocode}{suffix}.gz")

    # Read and cache the header separately
    header_chunk = pl.read_csv(
        file_path,
        separator="\t",
        n_rows=1
    )
    header = header_chunk.columns

    chunk_size = 1_000_000  # Adjust chunk size as needed (less than 1GB)

    yield "\t".join(header) + "\n"

    for chunk in read_in_chunks(file_path, chunk_size=chunk_size, header = header):
        filtered_chunk = process_and_filter_chunk(chunk, header=header)

        # Yield rows in the filtered chunk
        for row in filtered_chunk.iter_rows(named=False):
            yield "\t".join(map(str, row)) + "\n"

def getUnfilteredFunction(phenocode, suffix):
    
    column_dtypes = {
        0: str,   # chrom
        1: int,   # pos
        2: str,   # ref
        3: str,   # alt
        4: str,   # rsids
        5: str,   # nearest_genes
        6: str,   # test
        7: float, # pval
        8: float, # beta
        9: float, # sebeta
        10: float, # af
        11: float, # imp_quality
        12: int, # n_samples
    }
    
    def process_chunk(chunk, header):
        af_index = header.index('af')

        # Ensure MAF (modify the DataFrame, not Series directly)
        chunk = chunk.with_columns(
            pl.when(pl.nth(af_index) > 0.5)
            .then(1 - pl.nth(af_index))
            .otherwise(pl.nth(af_index))
            .alias("maf")
        )
        return chunk

    def read_in_chunks(file_path, chunk_size, header=None):
        # Read the file in chunks
        total_rows = 0
        while True:
            chunk = pl.read_csv(
                file_path,
                separator="\t",
                dtypes={col_name: column_dtypes[i] for i, col_name in enumerate(header)},  # Map columns by index
                skip_rows=total_rows,  # Skip rows processed in the previous chunks
                n_rows=chunk_size
            )
            if chunk.height == 0:  # No more data
                break
            total_rows += chunk.height
            yield chunk

    # Determine the file path based on `suffix`
    file_path = None
    if not suffix:
        file_path = os.path.join(get_pheweb_data_dir(), "pheno_gz", f"{phenocode}.gz")
    elif "interaction-" in suffix:
        file_path = os.path.join(get_pheweb_data_dir(), "interaction", f"{phenocode}{suffix}.gz")
    else:
        file_path = os.path.join(get_pheweb_data_dir(), "pheno_gz", f"{phenocode}{suffix}.gz")

    # Read the header separately
    header_chunk = pl.read_csv(
        file_path,
        separator="\t",
        n_rows=1  # Read only the first row for header
    )
    header = header_chunk.columns 
    chunk_size = 1_000_000  
    
    # Yield the header only once
    yield "\t".join(header) + "\n"

    # Process and yield chunks
    for chunk in read_in_chunks(file_path, chunk_size=chunk_size, header=header):
        # Process each chunk to calculate 'maf'
        chunk = process_chunk(chunk, header)
        
        # Yield rows of the chunk (skip header)
        for row in chunk.iter_rows(named=False):
            yield "\t".join(map(str, row)) + "\n"
