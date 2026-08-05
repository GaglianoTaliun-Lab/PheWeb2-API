from typing import List
import os

import shutil
from copy import deepcopy
import sqlite3
import json
import time

from .top_hits import run as top_hits_run
from ..file_utils import (write_json,
                          get_pheno_filepath,
                          get_filepath,
                          get_tmp_path,
                          write_heterogenous_variantfile,
                          get_matrices_filpaths,
                          backup_file,
                          read_maybe_gzip)
from ..utils import (get_phenotype_mask,
                     get_phenocode_mask,
                     get_phenotype_summary,
                     get_phenocode_with_suffixes,
                     PheWebError)

from .cffi._x import ffi, lib
from .matrix import create_matrix_tbi
from ..models.autocomplete_util import AutocompleteLoading


def chunk_sites(sites_filepath):
    """
    Chunking sites in size of 500_000. 
    """
    chunk_size = 500_000

    with read_maybe_gzip(sites_filepath) as f:
        line_count = sum(1 for _ in f)

    # not counting header
    line_count -= 1

    start = 0
    stop = chunk_size
    intervals = []

    while start < line_count:
        intervals.append((start, min(stop, line_count)))
        start = stop
        stop += chunk_size

    return intervals


def removing_single_files(phenocodes_to_remove) -> None:
    """
    Removing pheno filepath.
    """
    print("Removing single files...")

    file_types = {
        "interaction": "interaction",
        "interaction_tbi": "interaction",
        "manhattan": "manhattan",
        "parsed": "parsed",
        "pheno_gz": "pheno_gz",
        "pheno_gz_tbi": "pheno_gz",
        "qq": "qq",
        "best_of_pheno": "best_of_pheno"
    }

    for kind, backup_dir in file_types.items():
        for phenocode in phenocodes_to_remove:
            pheno_filepath = get_pheno_filepath(
                kind, phenocode, must_exist=False)

            if not os.path.exists(pheno_filepath):
                continue
            backup_file(pheno_filepath, backup_dir, "move")
            if os.path.exists(pheno_filepath):
                os.remove(pheno_filepath)

    print("Done.")


def filtering_pheno_file(phenotypes_to_remove) -> None:
    """
    filtering phenotypes.json and phenotypes.tsv
    """
    print("filtering phenotypes files...")

    phenos = get_phenotype_summary()

    # === filtering tsv ===
    out_filepath = get_filepath("phenotypes_summary_tsv")
    out_filepath_tmp = get_tmp_path(out_filepath)

    tsv_data = []

    for pheno in phenos:

        if get_phenocode_with_suffixes(pheno) in phenotypes_to_remove:
            continue

        tsv_data.append(pheno)

    write_heterogenous_variantfile(out_filepath_tmp, tsv_data, use_gzip=False)
    backup_file(out_filepath, "", "move")
    shutil.move(out_filepath_tmp, out_filepath)

    # === filtering json file ===
    out_filepath = get_filepath("phenotypes_summary")
    phenos_copy = deepcopy(phenos)

    for pheno in phenos_copy:
        if get_phenocode_with_suffixes(pheno) in phenotypes_to_remove:
            phenos.remove(pheno)

    del phenos_copy

    backup_file(out_filepath, "", "move")
    write_json(filepath=out_filepath, data=phenos, indent=3)

    print("Done.")


def filtering_best_pheno_by_gene(phenocodes_to_remove):
    print("filtering best-phenos-by-gene-sqlite3")
    best_phenos_by_gene_fp = get_filepath("best-phenos-by-gene-sqlite3")

    backup_file(best_phenos_by_gene_fp, "", "copy")

    conn = sqlite3.connect(best_phenos_by_gene_fp)
    cursor = conn.cursor()

    cursor.execute("SELECT gene, json FROM best_phenos_for_each_gene")
    rows = cursor.fetchall()

    for gene, json_text in rows:

        try:
            data = json.loads(json_text)

            if isinstance(data, list):
                cleaned_data = [
                    d for d in data
                    if ("phenocode" in d and d["phenocode"] not in phenocodes_to_remove)
                ]
            else:
                cleaned_data = data

            if cleaned_data != data:
                cursor.execute(
                    "UPDATE best_phenos_for_each_gene SET json = ? WHERE gene = ?",
                    (json.dumps(cleaned_data), gene)
                )
        except Exception as e:
            print(f"Error processing gene {gene}: {e}")
    conn.commit()
    conn.close()
    print("Done.")


def run(argv: List[str]) -> None:

    if "-h" in argv or "--help" in argv:
        print(
            "Removing phenotype specified in pheno-mask file."
        )
        exit(1)

    # # Phenotypes to remove
    phenotypes_to_remove = get_phenotype_mask()
    print(f"{len(phenotypes_to_remove)} phenotypes to remove.")
    phenotypes_to_remove = {get_phenocode_with_suffixes(
        pheno): pheno for pheno in phenotypes_to_remove}

    phenocodes_to_remove = get_phenocode_mask()

    failed_steps = {}

    # # ========== 1. Remove single files ==========
    # try:
    #     removing_single_files(phenocodes_to_remove)
    # except Exception as err:
    #     failed_steps["Removing single files"] = err

    # # ========== 2. filtering phenotype files ==========
    # try:
    #     filtering_pheno_file(phenotypes_to_remove)
    # except Exception as err:
    #     failed_steps["filtering phenotype files"] = err

    # # ========== 3. Rerunning top hits ==========
    # # Dependes on manhattan and phenotype file
    # print("Rerunning top-hits")
    # try:
    #     top_hits_run(["--force", "--remove"])
    # except Exception as err:
    #     failed_steps["rerunning top-hit"] = err

    # ========== 4. filtering sites and matrices ==========
    print("filtering sites and matrices...")
    try:
        start_time = time.time()

        # === Gathering filepaths ===
        unanno_fp = get_filepath("unanno", must_exist=False)
        unanno_tmp_fp = get_tmp_path(unanno_fp)
        sites_rsids_fp = get_filepath("sites-rsids", must_exist=False)
        sites_rsids_tmp_fp = get_tmp_path(sites_rsids_fp)
        sites_fp = get_filepath("sites", must_exist=False)
        sites_tmp_fp = get_tmp_path(sites_fp)

        sites_filepaths = [unanno_fp, sites_rsids_fp, sites_fp]
        sites_filepaths_str = ";".join(sites_filepaths)

        sites_tmp_filepaths = [unanno_tmp_fp, sites_rsids_tmp_fp, sites_tmp_fp]
        sites_tmp_filepaths_str = ";".join(sites_tmp_filepaths)

        matrices_filepaths = get_matrices_filpaths()
        matrices_tmp_filepaths = [get_tmp_path(
            fp) for fp in matrices_filepaths]
        matrices_filepaths_str = ";".join(matrices_filepaths)
        matrices_tmp_filepaths_str = ";".join(matrices_tmp_filepaths)

        phenocodes_to_remove_str = ";".join(phenocodes_to_remove)

        # === Filtering in cpp ===
        start_time = time.time()
        print("running cpp...")

        # This is reading site and matrix files in parallele.
        # Iterating through variants from site files and skipping fields for
        # phenotypes to remove.
        #
        # If a site is empty in every matrix, then removing everywhere.
        ret = lib.cffi_filter_matrices_and_sites(
            sites_filepaths_str.encode("utf8"),
            sites_tmp_filepaths_str.encode("utf8"),
            matrices_filepaths_str.encode("utf8"),
            matrices_tmp_filepaths_str.encode("utf8"),
            phenocodes_to_remove_str.encode("utf8"),
        )

        ret_bytes = ffi.string(ret, maxlen=1000)
        if ret_bytes != b"ok":
            raise PheWebError(
                "The portion written in c++/cffi failed with the message "
                + repr(ret_bytes)
            )
        t_time = time.time() - start_time
        print(f"Done. It tooks {t_time} seconds or {t_time/60} minutes.")

        # === Renaming/backup files ===
        print("Making backup, renaming tmp files and generating tabix files...")
        for s, site_fp in enumerate(sites_filepaths):

            site_tmp_fp = sites_tmp_filepaths[s]

            backup_file(site_fp, "sites", "move")
            shutil.move(site_tmp_fp, site_fp)

        for m, matrix_fp in enumerate(matrices_filepaths):

            matrix_tmp_fp = matrices_tmp_filepaths[m]

            backup_file(matrix_fp, "", "move")
            backup_file(matrix_fp + ".tbi", "", "move")

            shutil.move(matrix_tmp_fp,
                        matrix_fp)

            create_matrix_tbi(matrix_fp)
        print("Done.")
    except Exception as err:
        failed_steps["filtering matrices"] = err

    # ========== 5. Best pheno by gene ==========
    # try:
    #     filtering_best_pheno_by_gene(phenocodes_to_remove)
    # except Exception as err:
    #     failed_steps["filtering best_pheno_by_gene"] = err

    # # ========== 7. generate_autocomplete_db ==========
    # try:
    #     print("generate_autocomplete_db")
    #     AutocompleteLoading()
    #     print("Done.")
    # except Exception as err:
    #     failed_steps["AutocompleteLoading"] = err

    # # Printing any errors
    # if failed_steps:
    #     print("\nFollowing steps failed with error.")

    #     for step, err in failed_steps.items():
    #         print(step, ":", err, "\n")
