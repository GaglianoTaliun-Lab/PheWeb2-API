from .. import conf
from ..utils import get_phenocode_with_suffixes, get_phenotypes_to_process
from ..file_utils import (
    write_json,
    get_filepath,
    get_pheno_filepath,
    write_heterogenous_variantfile,
    backup_file
)

import os
import json
from pathlib import Path
from typing import Iterator, Dict, Any, List


def get_phenotypes_including_top_variants(existing_data) -> Iterator[Dict[str, Any]]:
    for pheno in get_phenotypes_to_process():

        if pheno in existing_data:
            continue

        with open(get_pheno_filepath("qq", pheno["phenocode"])) as f:
            # GC lambda 0.01 isn't set if it was infinite or otherwise broken.
            gc_lambda_hundred = json.load(
                f)["overall"]["gc_lambda"].get("0.01", None)

        with open(get_pheno_filepath("manhattan", pheno["phenocode"])) as f:
            variants = json.load(f)["unbinned_variants"]

        top_variant = min(variants, key=lambda v: v["pval"])
        num_peaks = sum(
            variant.get("peak", False) and variant["pval"] <= 5e-8
            for variant in variants
        )
        ret = {
            "phenocode": pheno["phenocode"],
            "pval": top_variant["pval"],
            "nearest_genes": top_variant["nearest_genes"],
            "chrom": top_variant["chrom"],
            "pos": top_variant["pos"],
            "ref": top_variant["ref"],
            "alt": top_variant["alt"],
            "rsids": top_variant["rsids"],
            "num_peaks": num_peaks,
            "gc_lambda_hundred": gc_lambda_hundred,  # numbers in keys break streamtable
        }
        for key in [
            "num_samples",
            "num_controls",
            "num_cases",
            "category",
            "phenostring",
        ]:
            if key in pheno:
                ret[key] = pheno[key]
        if isinstance(ret["nearest_genes"], list):
            ret["nearest_genes"] = ",".join(ret["nearest_genes"])
        yield ret


def get_phenotypes_including_top_variants_stratified(existing_data_with_suffix) -> Iterator[Dict[str, Any]]:
    for pheno in get_phenotypes_to_process():

        phenocode = get_phenocode_with_suffixes(pheno)

        if phenocode in existing_data_with_suffix:
            continue

        with open(get_pheno_filepath("manhattan", phenocode)) as f:
            variants = json.load(f)["unbinned_variants"]

        top_variant = min(variants, key=lambda v: v["pval"])
        num_peaks = sum(
            variant.get("peak", False) and variant["pval"] <= 5e-8
            for variant in variants
        )
        ret = {
            "phenocode": pheno["phenocode"],
            "pval": top_variant["pval"],
            "nearest_genes": top_variant["nearest_genes"],
            "chrom": top_variant["chrom"],
            "pos": top_variant["pos"],
            "ref": top_variant["ref"],
            "alt": top_variant["alt"],
            "rsids": top_variant["rsids"],
            "num_peaks": num_peaks,
            "stratification": pheno.get(
                "stratification", None
            ),  # will this put null if the column isn't even there?
            "interaction": pheno.get(
                "interaction", None
            ),  # will this put null if the column isn't even there?
        }

        for key in [
            "num_samples",
            "num_controls",
            "num_cases",
            "category",
            "phenostring",
        ]:
            if key in pheno:
                ret[key] = pheno[key]
        if isinstance(ret["nearest_genes"], list):
            ret["nearest_genes"] = ",".join(ret["nearest_genes"])
        yield ret


def should_run() -> bool:
    output_filepaths = [
        Path(get_filepath(name, must_exist=False))
        for name in ["phenotypes_summary", "phenotypes_summary_tsv"]
    ]
    if not all(fp.exists() for fp in output_filepaths):
        return True
    oldest_output_mtime = min(fp.stat().st_mtime for fp in output_filepaths)

    input_filepaths = []

    for pheno in get_phenotypes_to_process():
        phenocode = pheno["phenocode"]
        for strats in pheno["stratification"]:
            phenocode = phenocode + "." + pheno["stratification"][strats]
        input_filepaths.append(
            Path(get_pheno_filepath("manhattan", phenocode)))

    if not input_filepaths:
        return False

    newest_input_mtime = max(fp.stat().st_mtime for fp in input_filepaths)
    if newest_input_mtime > oldest_output_mtime:
        return True
    return False


def run(argv: List[str]) -> None:
    if "-h" in argv or "--help" in argv:
        print(
            "Make a file summarizing information about each phenotype (for use in the phenotypes table)"
        )
        exit(1)

    if not should_run():
        print("Already up-to-date!")
        return

    out_filepath = get_filepath("phenotypes_summary", must_exist=False)
    out_filepath_tsv = get_filepath("phenotypes_summary_tsv", must_exist=False)

    # Adding existing data if there is.
    existing_data = []
    if os.path.exists(out_filepath):
        with open(out_filepath, "r") as existing_f:
            existing_data = json.load(existing_f)

    existing_data_with_suffix = [get_phenocode_with_suffixes(d)
                                 for d in existing_data]

    if conf.has_stratifications():
        data = get_phenotypes_including_top_variants_stratified(
            existing_data_with_suffix)
    else:
        # TODO: Test this
        data = get_phenotypes_including_top_variants(existing_data)

    # Adding old data to new data and sorting based on pvalue
    data = sorted(list(existing_data) + list(data), key=lambda p: p["pval"])

    backup_file(out_filepath, "", "move")

    write_json(filepath=out_filepath, data=data)
    print("wrote {} phenotypes to {}".format(len(data), out_filepath))

    backup_file(out_filepath_tsv, "", "move")

    write_heterogenous_variantfile(out_filepath_tsv, data, use_gzip=False)
    print("wrote {} phenotypes to {}".format(len(data), out_filepath_tsv))
