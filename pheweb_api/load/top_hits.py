from ..utils import get_phenotype_mask, get_phenolist, get_phenotype_summary
from .. import conf
from ..file_utils import (
    write_json,
    write_heterogenous_variantfile,
    get_filepath,
    get_pheno_filepath,
    get_phenocode_with_stratifications,
)

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Iterator

# TODO: It'd be great if each peak also included a list of all the associations that it is masking, so that on-click we could display a variants-under-this-peak table.
# TODO: Somewhere have a user-extendable whitelist of info that should be copied about each pheno.  Copy all of that stuff.


def get_hits(pheno: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    if pheno["interaction"] is not None:
        pheno["phenocode"] += ".interaction-" + pheno["interaction"]
    if conf.has_stratifications():
        pheno["phenocode"] = get_phenocode_with_stratifications(pheno)

    with open(get_pheno_filepath("manhattan", pheno["phenocode"])) as f:
        variants = json.load(f)["unbinned_variants"]

    for v in variants:
        if v["pval"] <= conf.get_top_hits_pval_cutoff() and "peak" in v:
            v["phenocode"] = pheno["phenocode"].split(".")[0]
            for k in ["phenostring", "category", "interaction", "stratification"]:
                if k in pheno:
                    v[k] = pheno[k]
            yield v


def get_all_hits(phenos) -> List[Dict[str, Any]]:
    return sorted(
        (hit for pheno in phenos for hit in get_hits(pheno)),
        key=lambda hit: hit["pval"],
    )


def stringify_assocs(assocs: List[Dict[str, Any]]) -> None:
    for a in assocs:
        if isinstance(a.get("nearest_genes"), list):
            a["nearest_genes"] = ",".join(a["nearest_genes"])


def should_run(phenos) -> bool:
    output_filepaths = [
        Path(get_filepath(name, must_exist=False))
        for name in ["top-hits", "top-hits-1k", "top-hits-tsv"]
    ]
    print(f"{output_filepaths=}")
    if not all(fp.exists() for fp in output_filepaths):
        return True
    oldest_output_mtime = min(fp.stat().st_mtime for fp in output_filepaths)
    if conf.has_stratifications():
        input_filepaths = [
            Path(
                get_pheno_filepath(
                    "manhattan", get_phenocode_with_stratifications(pheno)
                )
            )
            for pheno in phenos
        ]
    else:
        input_filepaths = [
            Path(get_pheno_filepath("manhattan", pheno["phenocode"]))
            for pheno in phenos
        ]
    newest_input_mtime = max(fp.stat().st_mtime for fp in input_filepaths)
    if newest_input_mtime > oldest_output_mtime:
        return True
    return False


def run(argv: List[str]) -> None:
    out_filepath_json = get_filepath("top-hits", must_exist=False)
    out_filepath_1k_json = get_filepath("top-hits-1k", must_exist=False)
    out_filepath_tsv = get_filepath("top-hits-tsv", must_exist=False)

    parser = argparse.ArgumentParser(
        description="Make lists of top hits for this PheWeb.",
        add_help=False,
    )

    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-f', '--force', action='store_true')
    parser.add_argument('-r', "--remove", action='store_true')
    args = parser.parse_args(argv)

    if args.help:
        pvalue = "{:0.0e}".format(
            min(
                conf.get_top_hits_pval_cutoff(),
                conf.get_manhattan_peak_pval_threshold(),
            )
        ).replace("e-0", "e-")
        print(
            f"""
Make lists of top hits for this PheWeb in {out_filepath_json} and {out_filepath_tsv}.

To count as a top hit, a variant must:
- have a p-value < {pvalue}
- be among the top {conf.get_manhattan_num_unbinned()} associations in its phenotype
- have the smallest p-value within {conf.get_within_pheno_mask_around_peak()} bases within its phenotype (well, not exactly, but pretty much)

Some loci may have hits for multiple phenotypes.  If you want a list of loci with
just the top phenotype for each, use `pheweb top-loci`.
""")
        exit(1)

    if args.remove:
        phenos = get_phenotype_summary()
        mask = get_phenotype_mask()

        for pheno in mask:
            if pheno in phenos:
                phenos.remove(pheno)
    else:
        phenos = get_phenolist()

    if not args.force:
        if not should_run(phenos):
            print("Already up-to-date!")
            return

    hits = get_all_hits(phenos)

    write_json(filepath=out_filepath_json, data=hits, sort_keys=True)
    print("wrote {} hits to {}".format(len(hits), out_filepath_json))

    write_json(filepath=out_filepath_1k_json, data=hits[:1000], sort_keys=True)
    print("wrote {} hits to {}".format(len(hits[:1000]), out_filepath_1k_json))

    if hits:  # If there are no hits, we can't write a proper tsv
        stringify_assocs(hits)
        write_heterogenous_variantfile(out_filepath_tsv, hits, use_gzip=False)
        print("wrote {} hits to {}".format(len(hits), out_filepath_tsv))
