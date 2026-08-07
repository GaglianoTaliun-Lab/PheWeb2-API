import gzip
from pathlib import Path
import shutil
import os
import re
import pytest
import importlib
import json

from pheweb_api import conf
from pheweb_api.utils import PheWebError, get_phenocode_with_suffixes
from pheweb_api.file_utils import *

from pheweb_api.load.phenolist import run as run_phenolist
from pheweb_api.load.parse_input_files import run as run_parse_input_files


# ======== tearDown ========

@pytest.fixture
def use_tmp_path():
    """
    Generating a tmp generated-by-pheweb path to perform tests.
    generated-by-pheweb/tmp/generated-by-pheweb
    """

    # Save env and configs
    old_env = dict(os.environ)
    old_overrides = dict(conf.overrides)

    # Generate path to perform tests
    tmp_path = get_tmp_path("generated-by-pheweb")
    make_basedir(tmp_path)

    # Overwrites some env and configs
    os.environ['PHEWEB_DATA_DIR'] = tmp_path
    conf.overrides['PHEWEB_DATA_DIR'] = tmp_path
    conf.overrides["INTERACTION_TEST_NAME"] = "ADD-INT_SNPxsex"
    conf.overrides["ASSOC_TEST_NAME"] = "ADD-CONDTL"

    FIELD_ALIASES = {
        "CHROM": "chrom",  # Chromosome
        "GENPOS": "pos",  # Position
        "ALLELE0": "ref",  # Reference allele
        "ALLELE1": "alt",  # Effect (tested) allele
        "A1FREQ": "af",  # Frequency of the effect allele
        "N": "n_samples",  # Number of samples
        "BETA": "beta",  # Effect size
        "SE": "sebeta",  # Standard error of the effect
        "LOG10P": "pval",  # P-value
        "TEST": "test",  # Reported statistical test/model
        "INFO": "imp_quality",
    }

    conf.set_override("FIELD_ALIASES", FIELD_ALIASES)

    try:
        yield tmp_path
    finally:
        # Restore environment to avoid leaking into other tests
        os.environ.clear()
        os.environ.update(old_env)
        conf.overrides.clear()
        conf.overrides.update(old_overrides)
        shutil.rmtree(tmp_path)

# ======== FILE Generation ========


def dummy_summary_stats():

    summary_stat = get_generated_path("dummy.regenie.gz")

    header = "CHROM GENPOS ID ALLELE0 ALLELE1 A1FREQ A1FREQ_CASES A1FREQ_CONTROLS INFO N N_CASES N_CONTROLS TEST BETA SE CHISQ LOG10P EXTRA\n"
    line1 = "1 102915 1:102915:A:G A G 0.000277877 0.000128839 0.000318654 0.718271 26529 3395 23134 ADD-CONDTL -1.07588 0.852009 1.59454 0.684705 NA\n"
    line2 = "1 102915 1:102915:A:G A G 0.000277877 0.000128839 0.000318654 0.718271 26529 3395 23134 ADD-INT_SNP -6.59192 21.4266 0.0946487 0.120131 NA\n"
    line3 = "1 102915 1:102915:A:G A G 0.000277877 0.000128839 0.000318654 0.718271 26529 3395 23134 ADD-INT_SNPxsex 2.54078 10.7837 0.0555132 0.0895179 NA\n"
    line4 = "1 102915 1:102915:A:G A G 0.000277877 0.000128839 0.000318654 0.718271 26529 3395 23134 ADD-INT_2DF NA NA 1.42454 0.309335 NA"
    with gzip.open(summary_stat, "wt") as f:
        f.writelines([header, line1, line2, line3, line4])

    return summary_stat


def dummy_manifest_file(summary_stat):

    manifest = get_generated_path("manifest-example.csv")

    header = "phenocode,phenostring,assoc_files,num_samples,num_cases,num_controls,category,interaction,stratification.sex,stratification.ancestry\n"
    line1 = f"DUMMY_COM,dummy,{summary_stat},26529,3395,23134,dummy_category,,both,all\n"
    line2 = f"DUMMY_COM,dummy,{summary_stat},26529,3395,23134,dummy_category,sex,both,all\n"

    with open(manifest, "w") as f:
        f.writelines([header, line1, line2])

    return manifest

# ======== TEST FILE UTILS ========


def test_backup_file(use_tmp_path):

    data_dir = get_generated_path()

    # Test get_backup_path
    assert get_backup_path() == os.path.join(data_dir, "backups")

    # Test extract_data_subdir_from_filepath
    for subdir in data_subdirs:
        fake_path = os.path.join(data_dir, subdir, "example.txt")
        assert extract_data_subdir_from_filepath(fake_path) == subdir

    # Test config
    conf.overrides["ENABLE_BACKUPS"] = False
    phenolist = Path(get_filepath("phenolist", must_exist=False))
    phenolist.touch()
    phenolist_bckup = backup_file(str(phenolist), "", "copy")
    assert phenolist_bckup == ""

    conf.overrides["ENABLE_BACKUPS"] = True

    # Test methods
    # copy
    phenolist_bckup = Path(backup_file(str(phenolist), "", "copy"))
    assert phenolist_bckup.exists() and phenolist.exists()

    # move
    phenolist_bckup = Path(backup_file(str(phenolist), "", "move"))
    assert phenolist_bckup.exists() and not phenolist.exists()

    # Test add_iso_data
    def contains_iso(path: str) -> bool:
        pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+"
        return bool(re.search(pattern, path))

    assert contains_iso(str(phenolist_bckup))


# ==================== TEST FIRST TIME INGEST ====================


def test_first_time_ingest(use_tmp_path):
    """
    Testing a first time ingest with a single phenotype and a single site.
    Using stratification and interaction.
    """

    summary_stat = dummy_summary_stats()
    manifest_file = dummy_manifest_file(summary_stat)

    # === Testing phenolist ===
    run_phenolist([
        "import-phenolist",
        manifest_file,
        "-f",
        get_filepath("phenolist", must_exist=False)
    ])

    phenolist_fp = get_filepath("phenolist")

    assert os.path.exists(phenolist_fp)

    # asserting it contains summary_stat as assoc_file
    with open(phenolist_fp, "r") as f:
        data = json.load(f)
        assert data[0]["assoc_files"][0] == summary_stat

    dummy_phenocode = get_phenocode_with_suffixes(data[0])
    assert dummy_phenocode == "DUMMY_COM.all.both"

    dummy_interaction_phenocode = get_phenocode_with_suffixes(data[1])
    assert dummy_interaction_phenocode == "DUMMY_COM.interaction-sex.all.both"

    # # # === Testing parseinputfile ===
    run_parse_input_files([])

    dummy_parsed_fp = get_pheno_filepath("parsed", dummy_phenocode)
    assert Path(dummy_parsed_fp).exists()

    dummy_interaction_parsed_fp = get_pheno_filepath(
        "parsed", dummy_interaction_phenocode)
    assert Path(dummy_interaction_parsed_fp).exists()
