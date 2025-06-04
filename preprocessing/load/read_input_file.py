from ..utils import chrom_order, chrom_order_list, chrom_aliases, PheWebError
from .. import parse_utils
from .. import conf
from ..file_utils import read_maybe_gzip
from .load_utils import get_maf

import itertools
import re
import boltons.iterutils
import os
import pysam
import gc
import psutil 


class PhenoReader:
    """
    Reads variants (in order) and other info for a phenotype.
    It only returns variants that have a pvalue.
    If `minimum_maf` is defined, variants that don't meet that threshold (via MAF, AF, or AC/NS) are dropped.
    """

    def __init__(self, pheno, minimum_maf=0):
        field_aliases = conf.get_field_aliases()
        for alias, field_name in field_aliases.items():
            if isinstance(alias, str) and alias.startswith("file://") and field_name == "imp_quality":
                try:
                    file_path = alias.split(",")[0].split("file://")[1]
                    file_field_to_read = alias.split(",")[1]
                    self.r2_reader = R2FileReader(
                        filepath = file_path,
                        file_field_to_read = file_field_to_read,
                    )
                    self.use_external_r2 = True
                except Exception as e:
                    raise PheWebError(f"Failed to parse R2 file alias: {alias} — {e}")
                break

        self._pheno = pheno
        self._minimum_maf = minimum_maf or 0
        self.fields, self.filepaths = self._get_fields_and_filepaths(
            pheno["assoc_files"]
        )
        

    def get_variants(self):
        yield from self._order_refalt_lexicographically(
            itertools.chain.from_iterable(
                AssocFileReader(filepath=filepath, pheno=self._pheno, r2_reader=self.r2_reader, use_external_r2=True).get_variants(
                    minimum_maf=self._minimum_maf
                )
                for filepath in self.filepaths
            )
        )

    def get_info(self):
        infos = [
            AssocFileReader(filepath, self._pheno, r2_reader=None, use_external_r2=False).get_info()
            for filepath in self.filepaths
        ]
        for info in infos[1:]:
            if info != infos[0]:
                raise PheWebError(
                    "The pheno info parsed from some lines disagrees.\n"
                    + "- for the pheno {}\n".format(self._pheno["phenocode"])
                    + "- parsed from one line:\n    {}\n".format(infos[0])
                    + "- parsed another line:\n    {}\n".format(info)
                )
        return infos[0]

    def _order_refalt_lexicographically(self, variants):
        # Also assert that chrom and pos are in order
        cp_groups = itertools.groupby(variants, key=lambda v: (v["chrom"], v["pos"]))
        prev_chrom_index, prev_pos = -1, -1
        for cp, tied_variants in cp_groups:
            chrom_index = self._get_chrom_index(cp[0])
            if chrom_index < prev_chrom_index:
                raise PheWebError(
                    "The chromosomes in your file appear to be in the wrong order.\n"
                    + "The required order is: {!r}\n".format(chrom_order_list)
                    + "But in your file, the chromosome {!r} came after the chromosome {!r}\n".format(
                        cp[0], chrom_order_list[prev_chrom_index]
                    )
                )
            if chrom_index == prev_chrom_index and cp[1] < prev_pos:
                raise PheWebError(
                    "The positions in your file appear to be in the wrong order.\n"
                    + "In your file, the position {!r} came after the position {!r} on chromsome {!r}\n".format(
                        cp[1], prev_pos, cp[0]
                    )
                )
            prev_chrom_index, prev_pos = chrom_index, cp[1]
            for v in sorted(tied_variants, key=lambda v: (v["ref"], v["alt"])):
                yield v

    def _get_fields_and_filepaths(self, filepaths):
        # also sets `self._fields`

        assoc_files = [{"filepath": filepath} for filepath in filepaths]

        for assoc_file in assoc_files:
            ar = AssocFileReader(assoc_file["filepath"], self._pheno, r2_reader=None, use_external_r2=False)
            v = next(ar.get_variants())
            assoc_file["chrom"], assoc_file["pos"] = v["chrom"], v["pos"]
            assoc_file["fields"] = list(v)
        assert boltons.iterutils.same(af["fields"] for af in assoc_files)
        assoc_files = sorted(assoc_files, key=self._variant_chrpos_order_key)
        return (
            assoc_files[0]["fields"],
            [assoc_file["filepath"] for assoc_file in assoc_files],
        )

    @staticmethod
    def _variant_chrpos_order_key(v):
        return (PhenoReader._get_chrom_index(v["chrom"]), v["pos"])

    @staticmethod
    def _get_chrom_index(chrom):
        try:
            return chrom_order[chrom]
        except KeyError:
            raise PheWebError(
                "It looks like one of your variants has the chromosome {!r}, but PheWeb doesn't handle that chromosome.\n".format(
                    chrom
                )
                + "I bet you could fix it by running code like this on each of your input files:\n"
                + "zless my-input-file.tsv | perl -nale 'print if $. == 1 or m{^(1?[0-9]|2[0-2]|X|Y|MT?)\t}' | gzip > my-replacement-input-file.tsv.gz\n"
            )


class AssocFileReader:
    # TODO: Dec 2024 : this could be way faster with polars.
    """Has no concern for ordering, only in charge of parsing one associations file."""

    # TODO: use `pandas.read_csv(src_filepath, usecols=[...], converters={...}, iterator=True, verbose=True, na_values='.', sep=None)
    #   - first without `usecols`, to parse the column names, and then a second time with `usecols`.

    def __init__(self, filepath, pheno, r2_reader=None, use_external_r2: bool = False):
        self.filepath = filepath
        self._pheno = pheno
        self._interaction = pheno["interaction"]
        self.r2_reader = r2_reader
        self.use_external_r2 = use_external_r2 # bool to indicate if the R2 values are read from an external file


    def get_variants(self, minimum_maf=0, use_per_pheno_fields=False):
        if use_per_pheno_fields:
            fieldnames_to_check = [
                fieldname
                for fieldname, fieldval in parse_utils.per_pheno_fields.items()
                if fieldval["from_assoc_files"]
            ]
        else:
            fieldnames_to_check = [
                fieldname
                for fieldname, fieldval in itertools.chain(
                    parse_utils.per_variant_fields.items(),
                    parse_utils.per_assoc_fields.items(),
                )
                if fieldval["from_assoc_files"]
            ]

        interaction_aliases = conf.get_interaction_aliases()
        if interaction_aliases is not None:
            pre_mapped_interaction = {v: k for k, v in interaction_aliases.items()}
        else:
            pre_mapped_interaction = {self._interaction : self._interaction}
            
        with read_maybe_gzip(self.filepath) as f:
            try:
                header_line = next(f)
            except Exception as exc:
                raise PheWebError(
                    "Failed to read from file {} - is it empty?".format(self.filepath)
                ) from exc

            if header_line.count("\t") >= 4:
                delimiter = "\t"
            elif header_line.count(" ") >= 4:
                delimiter = " "
            elif header_line.count(",") >= 4:
                delimiter = ","
            else:
                raise PheWebError(
                    "Cannot guess what delimiter to use to parse the header line {!r} in file {!r}".format(
                        header_line, self.filepath
                    )
                )

            colnames = [
                colname.strip("\"' ").lower()
                for colname in header_line.rstrip("\n\r").split(delimiter)
            ]
            colidx_for_field = self._parse_header(colnames, fieldnames_to_check)
            # Special case for `MARKER_ID`
            if "marker_id" not in colnames:
                marker_id_col = None
            else:
                marker_id_col = colnames.index("marker_id")
                colidx_for_field["ref"] = (
                    None  # This is just to mark that we have 'ref', but it doesn't come from a column.
                )
                colidx_for_field["alt"] = None
                # TODO: this sort of provides a mapping for chrom and pos, but those are usually doubled anyways.
                # TODO: maybe we should allow multiple columns to map to each key, and then just assert that they all agree.
            self._assert_all_fields_mapped(
                colnames, fieldnames_to_check, colidx_for_field
            )

            if use_per_pheno_fields:
                for line in f:
                    values = line.rstrip("\n\r").split(delimiter)
                    variant = self._parse_variant(values, colnames, colidx_for_field)
                    yield variant

            else:
                for line in f:
                    values = line.rstrip("\n\r").split(delimiter)
                    variant = self._parse_variant(values, colnames, colidx_for_field)

                    test_value = variant.get("test", "")

                    imp_quality = variant.get("imp_quality")
                    # Retrieve and check imputation quality
                    if imp_quality is None:
                        if self.r2_reader is not None and self.use_external_r2 == True:
                            # if external r2 file is provided, use the R2 value from the external file
                            r2 = self.r2_reader.get_r2_value(variant['chrom'], variant['pos'], variant['ref'], variant['alt'])
                            
                            if r2 is None or r2 < conf.get_min_imp_quality():
                                continue
                            else:
                                variant['imp_quality'] = r2
                    else:
                        if imp_quality == "NA" or not isinstance(imp_quality, float):
                            continue
                        elif imp_quality < conf.get_min_imp_quality():
                            continue

                    if self._interaction:
                        if (
                            f"ADD-INT_SNPx{pre_mapped_interaction[self._interaction]}"
                            not in test_value
                        ):
                            continue
                        
                        if conf.get_interaction_maf_threshold() and conf.get_interaction_mac_threshold():
                            raise ValueError(
                                (
                                    "Both MAC and MAF threshold are set, which is not allowed. Only set one and re-run."
                                )
                            )
                            
                        maf = get_maf(variant, self._pheno)
                        if maf is not None and conf.get_interaction_maf_threshold() and maf < conf.get_interaction_maf_threshold():
                            continue
                        
                        mac = maf * variant.get("n_samples") * 2 # times 2 because of the 2 alleles
                        if conf.get_interaction_mac_threshold() is not None and mac < conf.get_interaction_mac_threshold():
                            continue
                        
                    elif test_value not in {"ADD", "ADD-CONDTL"}:
                        continue

                    # Skip processing further if `pval` is empty
                    if not variant.get("pval"):
                        continue

                    # Retrieve and check minor allele frequency (MAF) of non-interaction testing early to avoid unnecessary processing
                    if not self._interaction:
                        maf = get_maf(variant, self._pheno)
                        if maf is not None and maf < minimum_maf:
                            continue

                    # Parse marker ID only if necessary
                    if marker_id_col is not None:
                        chrom2, pos2, variant["ref"], variant["alt"] = (
                            AssocFileReader.parse_marker_id(values[marker_id_col])
                        )
                        if variant["chrom"] != chrom2 or variant["pos"] != pos2:
                            raise AssertionError(
                                (
                                    values,
                                    variant,
                                    chrom2 if variant["chrom"] != chrom2 else pos2,
                                )
                            )

                    # Use alias replacement only if the chromosome is in the aliases dictionary
                    variant["chrom"] = chrom_aliases.get(
                        variant["chrom"], variant["chrom"]
                    )

                    yield variant

    def get_info(self):
        infos = []
        for linenum, variant in enumerate(
            itertools.islice(self.get_variants(use_per_pheno_fields=True), 0, 1000)
        ):
            # Check that num_cases + num_controls == num_samples
            if all(
                key in variant for key in ["num_cases", "num_controls", "num_samples"]
            ):
                if (
                    variant["num_cases"] + variant["num_controls"]
                    != variant["num_samples"]
                ):
                    raise PheWebError(
                        "The number of cases and controls don't add up to the number of samples on one line in one of your association files.\n"
                        + "- the filepath: {!r}\n".format(self.filepath)
                        + "- the line number: {}".format(linenum + 1)
                        + "- parsed line: [{!r}]\n".format(variant)
                    )
                del variant["num_samples"]  # don't need it.
            infos.append(variant)
        for info in infos[1:]:
            if info != infos[0]:
                raise PheWebError(
                    "The pheno info parsed from some lines disagrees.\n"
                    + "- in the file {}".format(self.filepath)
                    + "- parsed from first line:\n    {}".format(infos[0])
                    + "- parsed from a later line:\n    {}".format(info)
                )
        return infos[0]

    def _parse_variant(self, values, colnames, colidx_for_field):
        # `values`: [str]

        if len(values) != len(colnames):
            repr_values = repr(values)
            if len(repr_values) > 5000:
                repr_values = (
                    repr_values[:200] + " ... " + repr_values[-200:]
                )  # sometimes we get VERY long strings of nulls.
            raise PheWebError(
                "ERROR: A line has {!r} values, but we expected {!r}.\n".format(
                    len(values), len(colnames)
                )
                + "- The line: {}\n".format(repr_values)
                + "- The header: {!r}\n".format(colnames)
                + "- In file: {!r}\n".format(self.filepath)
            )

        variant = {}
        for field, colidx in colidx_for_field.items():
            if colidx is not None:
                parse = parse_utils.parser_for_field[field]
                value = values[colidx]
                try:
                    variant[field] = parse(value)
                except Exception as exc:
                    raise PheWebError(
                        "failed on field {!r} attempting to convert value {!r} to type {!r} with constraints {!r} in {!r} on line with values {!r} given colnames {!r} and field mapping {!r}".format(
                            field,
                            values[colidx],
                            parse_utils.fields[field]["type"],
                            parse_utils.fields[field],
                            self.filepath,
                            values,
                            colnames,
                            colidx_for_field,
                        )
                    ) from exc

        return variant

    def _parse_header(self, colnames, fieldnames_to_check):
        colidx_for_field = {}  # which column (by number, not name) holds the value for the field (the key)
        field_aliases = conf.get_field_aliases()  # {alias: field_name}
        
        for colidx, colname in enumerate(colnames):
            if (
                colname in field_aliases
                and field_aliases[colname] in fieldnames_to_check
            ):
                field_name = field_aliases[colname]
                if any(alias.startswith("file://") for alias in field_aliases) and field_name == "imp_quality":
                    # skip the imp_quality field if it is linked to a file, default using the INFO field
                    continue

                if field_name in colidx_for_field:
                    raise PheWebError(
                        "PheWeb found two different ways of mapping the field_name {!r} to the columns {!r}.\n".format(
                            field_name, colnames
                        )
                        + "field_aliases = {!r}.\n".format(field_aliases)
                        + "File = {}\n".format(self.filepath)
                    )
                colidx_for_field[field_name] = colidx
        return colidx_for_field

    def _assert_all_fields_mapped(
        self, colnames, fieldnames_to_check, colidx_for_field
    ):
        fields = parse_utils.fields
        required_fieldnames = [
            fieldname
            for fieldname in fieldnames_to_check
            if fields[fieldname]["required"]
        ]
        missing_required_fieldnames = [
            fieldname
            for fieldname in required_fieldnames
            if fieldname not in colidx_for_field
        ]
        if missing_required_fieldnames:
            err_message = (
                "Some required fields weren't successfully mapped to the columns of an input file.\n"
                + "The file is {!r}.\n".format(self.filepath)
                + "The fields that were required but not present are: {!r}\n".format(
                    missing_required_fieldnames
                )
                + "field_aliases = {}:\n".format(conf.get_field_aliases())
                + "Here are all the column names from that file: {!r}\n".format(
                    colnames
                )
            )
            if colidx_for_field:
                err_message += (
                    "Here are the fields that successfully mapped to columns of the file:\n"
                    + "".join(
                        "- {}: {} (column #{})\n".format(
                            field, colnames[colidx], colidx
                        )
                        for field, colidx in colidx_for_field.items()
                    )
                )
            else:
                err_message += "No fields successfully mapped.\n"
            err_message += "You need to modify your input files or set field_aliases in your `config.py`."
            raise PheWebError(err_message)

    @staticmethod
    def parse_marker_id(marker_id):
        match = AssocFileReader.parse_marker_id_regex.match(marker_id)
        if match is None:
            raise PheWebError(
                "ERROR: MARKER_ID didn't match our MARKER_ID pattern: {!r}".format(
                    marker_id
                )
            )
        chrom, pos, ref, alt = match.groups()
        return chrom, int(pos), ref, alt

    parse_marker_id_regex = re.compile(r"([^:]+):([0-9]+)_([-ATCG\.]+)/([-ATCG\.\*]+)")

class R2FileReader:
    """
    Reads R2 values from external vcf or pvar file and stores them in a dictionary.
    """
    def __init__(self, filepath, file_field_to_read):
        self.filepath = filepath
        self.variants_buffer = dict()
        self.file_field_to_read = file_field_to_read
        self.min_imp_quality = conf.get_min_imp_quality()
        # print(f"[DEBUG]===> min_imp_quality: {self.min_imp_quality}")

        # TODO: in documentation, the r2 file should be one concatenated file with all chromosomes (either pvar or vcf.gz)
        # TODO: check if the file is exists; if it is VCF/BCF, then check if index file is exists
        if not self.filepath.endswith(".pvar"):
            if not self.filepath.endswith(".vcf.gz"):
                raise Exception(f"Invalid file extension: {self.filepath}")
            elif not os.path.exists(self.filepath + ".tbi"):
                raise Exception(f"Index file does not exist: {self.filepath}.tbi")
            
        self.loaded_chr = None
        # self.loaded_start_pos = None
        # self.loaded_end_pos = None

    def get_r2_value(self, chrom, pos, ref, alt):
        if chrom != self.loaded_chr:
            self.read_r2_file(chrom) # update your variants_buffer
        #TODO: maybe enable chunk of chromosomes in the future
        #if pos < self.loaded_start_pos or pos > self.loaded_end_pos:
        #   self.loaded_start_pos = pos - 1;
        #   self.loaded_end_pos = pos + 500000;

        return self.variants_buffer.get((pos, ref, alt), None)
    

    def read_r2_file(self, chrom: str) -> None:

        # Clear previous chromosome data to free memory
        if self.variants_buffer:
            self.variants_buffer.clear()
        
        if self.filepath.endswith(".pvar"):
            if chrom == '23': # Regenie v4 collapses 23, X, Y, PAR1 and PAR2 into single chromosome 23 in output when working with PGEN input
                self.read_pvar_file(self.filepath, {'PAR1', 'PAR2', 'X', 'Y'})
            else:
                self.read_pvar_file(self.filepath, chrom)
        else:
            if chrom == '23': # Regenie v4 collapses 23, X, Y, PAR1 and PAR2 into single chromosome 23 in output when working with PGEN input
                print(f'===> reading vcf file for chromosome {chrom}')
                self.read_vcf_file(self.filepath, 'X')
            else:
                print(f'===> reading vcf file for chromosome {chrom}')
                self.read_vcf_file(self.filepath, chrom)
        self.loaded_chr = chrom
        
    def read_vcf_file(self, file: str, chrom: str) -> None: # TODO: make sure this function is sync.with the read_pvar_file 
        with pysam.VariantFile(file, drop_samples=True) as vcf:
            for record in vcf.fetch(f'chr{chrom}'):
                assert not record.samples, f"Variant {record.id} unexpectedly has samples"
                r2 = round(record.info.get(self.file_field_to_read), 2) if record.info.get(self.file_field_to_read) is not None else None
                if r2 is None or r2 < self.min_imp_quality:
                    continue
                self.variants_buffer[(record.pos, record.ref, record.alts[0])] = r2
    
    def read_pvar_file(self, file: str) -> None:
        # TODO: implement this function to be sync. with read_vcf_file
        pass
    #     with open(file, 'r') as f:
    #         for line in f:
    #             if line.startswith('##'):
    #                 continue
    #             if line.startswith('#CHROM'):
    #                 fields_header = line.strip().split()
    #                 continue  

    #             fields = line.strip().split()
    #             if len(fields) < 6:
    #                 assert False, f"Malformed line: {line}"

    #             info = fields[5]
    #             info_fields = info.split(';')
    #             r2_field = next((field for field in info_fields if field.startswith(f'{self.file_field_to_read}=')), None)

    #             if r2_field is None:
    #                 continue 

    #             try:
    #                 r2 = float(r2_field.split('=')[1])
    #             except ValueError:
    #                 # assert False, f"Invalid R2 value: {r2_field}"
    #                 continue 

    #             if r2 < 0.3:
    #                 continue

    #             chrom = fields[fields_header.index('#CHROM')]
    #             if chrom.startswith('PAR') or chrom.startswith('X'):
    #                 chrom = '23'
    #             pos = fields[fields_header.index('POS')]
    #             ref = fields[fields_header.index('REF')]
    #             alt = fields[fields_header.index('ALT')].split(',')[0]

    #             variant_id = f"{chrom}:{pos}:{ref}:{alt}"
    #             self.variants[variant_id] = r2
    
 
            
