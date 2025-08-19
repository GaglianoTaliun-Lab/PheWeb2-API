from typing import List, Dict, Optional, Any, Iterator
from pheweb_api import parse_utils
from flask import current_app
import math
from contextlib import contextmanager


import itertools
import gzip
import io
import csv
import os
import pysam

csv.register_dialect(
    "pheweb-internal-dialect",
    delimiter="\t",
    doublequote=False,
    escapechar="\\",
    lineterminator="\n",
    quotechar='"',
    skipinitialspace=False,
    strict=True,
)


@contextmanager
def read_gzip(filepath):  # mypy doesn't like it
    # hopefully faster than `gzip.open(filepath, 'rt')` -- TODO: find out whether it is
    with gzip.GzipFile(
        filepath, "rb"
    ) as f:  # leave in binary mode (default), let TextIOWrapper decode
        with io.BufferedReader(f, buffer_size=2**18) as g:  # 256KB buffer
            with io.TextIOWrapper(g) as h:  # bytes -> unicode
                yield h


class _Get_Pheno_Region:
    @staticmethod
    def _rename(d: dict, oldkey, newkey):
        d[newkey] = d[oldkey]
        del d[oldkey]

    @staticmethod
    def _dataframify(list_of_dicts: List[Dict[Any, Any]]) -> Dict[Any, list]:
        """converts [{a:1,b:2}, {a:11,b:12}] -> {a:[1,11], b:[2,12]}"""
        keys = set(itertools.chain.from_iterable(list_of_dicts))
        dataframe: Dict[Any, list] = {k: [] for k in keys}
        for d in list_of_dicts:
            for k, v in d.items():
                dataframe[k].append(v)
        return dataframe

    @staticmethod
    def get_pheno_region(
        phenocode: str, chrom: str, pos_start: int, pos_end: int
    ) -> dict:
        variants = []
        with IndexedVariantFileReader(phenocode) as reader:
            for v in reader.get_region(chrom, pos_start, pos_end + 1):
                v["id"] = "{chrom}:{pos}_{ref}/{alt}".format(**v)
                # TODO: change JS to make these unnecessary
                v["end"] = v["pos"]
                _Get_Pheno_Region._rename(v, "chrom", "chr")
                _Get_Pheno_Region._rename(v, "pos", "position")
                _Get_Pheno_Region._rename(v, "rsids", "rsid")
                _Get_Pheno_Region._rename(v, "pval", "pvalue")
                variants.append(v)

        df = _Get_Pheno_Region._dataframify(variants)

        max_log10p = -math.log10(min(df["pvalue"]))

        df["max_log10p"] = max_log10p

        return {
            "data": df,
            "lastpage": None,
        }


get_pheno_region = _Get_Pheno_Region.get_pheno_region


@contextmanager
def IndexedVariantFileReader(phenocode: str):
    filepath = os.path.join(current_app.config["PHENO_GZ_DIR"], phenocode + ".gz")
    # filepath = get_pheno_filepath('pheno_gz', phenocode)
    with read_gzip(filepath) as f:
        reader: Iterator[List[str]] = csv.reader(f, dialect="pheweb-internal-dialect")
        fields = next(reader)
    if fields[0].startswith(
        "#"
    ):  # previous version of PheWeb commented the header line
        fields[0] = fields[0][1:]

    for field in fields:
        assert (
            field in parse_utils.per_variant_fields or field in parse_utils.per_assoc_fields
        ), field
    colidxs = {field: idx for idx, field in enumerate(fields)}
    with pysam.TabixFile(filepath, parser=None) as tabix_file:
        yield _ivfr(tabix_file, colidxs)


class _ivfr:
    def __init__(self, _tabix_file: pysam.TabixFile, _colidxs: Dict[str, int]):
        self._tabix_file = _tabix_file
        self._colidxs = _colidxs

    def _parse_variant_row(self, variant_row: List[str]) -> Dict[str, Any]:
        variant = {}
        for field in self._colidxs:
            val = variant_row[self._colidxs[field]]
            parser = parse_utils.reader_for_field[field]
            try:
                variant[field] = parser(val)
            except Exception:
                # TODO: replace this properly?
                raise Exception(
                    "ERROR: Failed to parse the value {!r} for field {!r} in file {!r}".format(
                        val, field, self._tabix_file.filename
                    )
                )
                # raise PheWebError('ERROR: Failed to parse the value {!r} for field {!r} in file {!r}'.format(val, field, self._tabix_file.filename)) from exc
        return variant

    def get_region(self, chrom: str, start: int, end: int) -> Iterator[Dict[str, Any]]:
        """
        includes `start`, does not include `end`
        return is like [{
              'chrom': 'X', 'pos': 43254, ...,
            }, ...]
        """
        if start < 1:
            start = 1
        if start >= end:
            return []
        if chrom not in self._tabix_file.contigs:
            return []

        # I do not understand why I need to use `pos-1`.
        # The pysam docs talk about being zero-based or one-based. Is this what they're referring to?
        # Doesn't make much sense to me.  There must be a reason that I don't understand.

        try:
            tabix_iter = self._tabix_file.fetch(chrom, start - 1, end - 1, parser=None)
        except Exception as exc:
            raise Exception(
                "ERROR when fetching {}-{}-{} from {}".format(
                    chrom, start - 1, end - 1, self._tabix_file.filename
                )
            ) from exc
        reader: Iterator[List[str]] = csv.reader(
            tabix_iter, dialect="pheweb-internal-dialect"
        )
        for variant_row in reader:
            yield self._parse_variant_row(variant_row)

    def get_variant(
        self, chrom: str, pos: int, ref: str, alt: int
    ) -> Optional[Dict[str, Any]]:
        x = self.get_region(chrom, pos, pos + 1)
        for variant in x:
            if variant["pos"] != pos:
                # print('WARNING: while looking for variant {}-{}-{}-{}, saw {!r}'.format(chrom, pos, ref, alt, variant))
                continue
            if variant["ref"] == ref and variant["alt"] == alt and variant:
                return variant
        return None
