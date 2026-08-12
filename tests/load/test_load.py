from pathlib import Path
import shutil
import os
import re
import pytest
import json
import sqlite3

from pheweb_api import conf
from pheweb_api.utils import *
from pheweb_api.file_utils import *

from pheweb_api.load.phenolist import run as run_phenolist
from pheweb_api.load.parse_input_files import run as run_parse_input_files
from pheweb_api.load.sites import run as run_sites
from pheweb_api.load.add_rsids import run as run_add_rsids
from pheweb_api.load.add_genes import run as run_add_genes
from pheweb_api.load.make_cpras_rsids_sqlite3 import run as run_make_cpras_rsids_sqlite3
from pheweb_api.load.augment_phenos import run as run_augment_phenos
from pheweb_api.load.matrix import run as run_matrix
from pheweb_api.load.gather_pvalues_for_each_gene import run as run_gather_pvalues_for_each_gene
from pheweb_api.load.manhattan import run as run_manhattan
from pheweb_api.load.qq import run as run_qq
from pheweb_api.load.phenotypes import run as run_phenotypes
from pheweb_api.load.top_hits import run as run_top_hits
from pheweb_api.load.best_of_pheno import run as run_best_of_pheno
from pheweb_api.load.process_assoc_files import run as run_process_assoc_files
from pheweb_api.models.autocomplete_util import AutocompleteLoading

from dummy_data import *

# ==================== tearDown ====================


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
    conf.overrides["PVAL_IS_NEGLOG10"] = True

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


# ==================== TEST FILE UTILS ====================


def test_backup_file(use_tmp_path):
    """
    Testing file backup fonctionnalities
    1. extracting subdir from filepath.
    2. Testing ENABLE_BACKUPS set to false doesn't backup anything.
    3-4. Testing copy and move backup methods.
    5. Testing adding iso to filepath. 
    """

    print("==================== TEST BACKUP FILE FEATURE ====================")

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

    print("==================== TEST FIRST TIME INGEST ====================")

    summary_stat = dummy_summary_stats()
    manifest_file = dummy_manifest_file(summary_stat)

    # ======== Testing phenolist ========
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

    # ======== Testing parseinputfile ========
    run_parse_input_files([])

    dummy_parsed_fp = get_pheno_filepath("parsed", dummy_phenocode)
    assert Path(dummy_parsed_fp).exists()

    dummy_interaction_parsed_fp = get_pheno_filepath(
        "parsed", dummy_interaction_phenocode)
    assert Path(dummy_interaction_parsed_fp).exists()

    # === Testing sites ===
    run_sites([])

    uanno_fp = get_filepath("unanno")

    assert Path(uanno_fp).exists()

    with VariantFileReader(uanno_fp) as uanno_file:

        variant = next(iter(uanno_file))

        assert variant["chrom"] == "19"
        assert variant["pos"] == 44908822
        assert variant["ref"] == "C"
        assert variant["alt"] == "T"

    # ======== Testing gene aliases ========
    # NOTE: This is not testing the real feature as the real one requires internet and takes time.
    # Instead generating a dummy db with dummy_gene_aliases function containing a single ().

    gene_aliases_fp = dummy_gene_aliases()
    assert Path(gene_aliases_fp).exists()

    # ======== Testing add_rsids ========
    # NOTE: This is not testing the real feature as the real one requires internet and takes time.
    # Instead generating a dummy rsid ressource with dummy_rsids function.

    dummy_rsids_filepath = dummy_rsids()

    run_add_rsids([])

    sites_rsids_filepath = get_filepath("sites-rsids", must_exist=False)
    assert Path(sites_rsids_filepath).exists()

    with VariantFileReader(sites_rsids_filepath) as sites_rsids_file:

        variant = next(iter(sites_rsids_file))

        assert variant["chrom"] == "19"
        assert variant["pos"] == 44908822
        assert variant["ref"] == "C"
        assert variant["alt"] == "T"
        assert variant["rsids"] == "rs7412"

    # ======== Testing add_genes ========
    # NOTE: This is not testing the real feature as the real one requires internet and takes time.
    # Instead generating a dummy gene ressource with dummy_genes function.

    dummy_genes()

    run_add_genes([])

    sites_filepath = get_filepath("sites", must_exist=False)
    assert Path(sites_filepath).exists()

    with VariantFileReader(sites_filepath) as sites_file:

        variant = next(iter(sites_file))

        assert variant["chrom"] == "19"
        assert variant["pos"] == 44908822
        assert variant["ref"] == "C"
        assert variant["alt"] == "T"
        assert variant["rsids"] == "rs7412"
        assert variant["nearest_genes"] == "APOE"

    # ======== Testing make_cpras_rsids_sqlite3 ========
    run_make_cpras_rsids_sqlite3([])

    cpras_rsids_filepath = get_filepath("cpras-rsids-sqlite3")

    assert Path(cpras_rsids_filepath).exists()

    cpras_rsids_db = sqlite3.connect(cpras_rsids_filepath)
    cur = cpras_rsids_db.cursor()

    cur.execute("SELECT * FROM cpras_rsids")
    cpras_rsids = cur.fetchone()

    assert cpras_rsids == ('19-44908822-C-T', 'rs7412')

    # ======== Testing augment_phenos ========

    run_augment_phenos([])

    dummy_pheno_gz_filepath = get_pheno_filepath("pheno_gz", dummy_phenocode)
    assert Path(dummy_pheno_gz_filepath).exists()

    dummy_interaction_filepath = get_pheno_filepath(
        "interaction", dummy_interaction_phenocode)
    assert Path(dummy_interaction_filepath).exists()

    # ======== Testing matrix ========
    run_matrix([])

    stratification_paths = get_stratification_paths(
        get_phenolist_no_interaction())

    matrix_gz_stratified_filepath = get_pheno_filepath(
        "matrix-stratified", stratification_paths[0], must_exist=False
    )

    assert Path(matrix_gz_stratified_filepath).exists()
    assert Path(matrix_gz_stratified_filepath + ".tbi").exists()

    assert MatrixReader(matrix_gz_stratified_filepath).get_phenocodes()[0] == \
        "DUMMY_COM.all.both"

    # ======== Testing gather_pvalues_for_each_gene ========
    run_gather_pvalues_for_each_gene([])

    best_phenos_by_gene_filepath = Path(get_filepath(
        "best-phenos-by-gene-sqlite3", must_exist=False))

    best_phenos_by_gene_db = sqlite3.connect(str(best_phenos_by_gene_filepath))
    cur = best_phenos_by_gene_db.cursor()
    cur.execute("SELECT * FROM best_phenos_for_each_gene")
    best_phenos_for_each_gene = cur.fetchone()

    expected = ("APOE",
                '[{"test": "ADD-CONDTL", "category": "dummy_category", "interaction": "sex", "num_cases": "", "num_controls": "", "num_samples": 26392, "phenocode": "DUMMY_COM.all.both", "phenostring": "dummy", "stratification": {"ancestry": "all", "sex": "both"}, "pval": 2.7e-69, "beta": -0.27, "sebeta": 0.016, "af": 0.081, "imp_quality": 1.00121, "n_samples": 26392, "distance_to_true_start": 3031, "is_in_real_range": true}]')
    assert best_phenos_for_each_gene == expected

    # ======== Testing manhattan ========
    run_manhattan([])

    manhattan_filepath = get_pheno_filepath("manhattan", dummy_phenocode)

    assert Path(manhattan_filepath).exists()

    manhattan_interaction_filepath = get_pheno_filepath(
        "manhattan", dummy_interaction_phenocode)

    assert Path(manhattan_interaction_filepath).exists()

    with open(manhattan_filepath, "r") as manhattan_file:
        data = json.load(manhattan_file)
        assert len(data["unbinned_variants"]) == 1
        variant = data["unbinned_variants"][0]
        assert variant["chrom"] == "19"
        assert variant["pos"] == 44908822
        assert variant["ref"] == "C"
        assert variant["alt"] == "T"
        assert variant["rsids"] == "rs7412"
        assert variant["nearest_genes"] == "APOE"
        assert variant["pval"] == 2.7e-69

    with open(manhattan_interaction_filepath, "r") as manhattan_interaction_file:
        data = json.load(manhattan_interaction_file)
        assert len(data["unbinned_variants"]) == 1
        variant = data["unbinned_variants"][0]
        assert variant["chrom"] == "19"
        assert variant["pos"] == 44908822
        assert variant["ref"] == "C"
        assert variant["alt"] == "T"
        assert variant["rsids"] == "rs7412"
        assert variant["nearest_genes"] == "APOE"
        assert variant["pval"] == 1.1e-8

    # ======== Testing qq ========

    run_qq([])

    qq_filepath = get_pheno_filepath("qq", dummy_phenocode)

    assert Path(qq_filepath).exists()

    qq_interaction_filepath = get_pheno_filepath(
        "qq", dummy_interaction_phenocode)

    assert Path(qq_interaction_filepath).exists()

    # ======== Testing phenotypes ========

    run_phenotypes([])

    phenotypes_filepath = get_filepath("phenotypes_summary", must_exist=False)
    phenotypes_tsv_filepath = get_filepath(
        "phenotypes_summary_tsv", must_exist=False)

    assert Path(phenotypes_filepath).exists()
    assert Path(phenotypes_tsv_filepath).exists()

    with open(phenotypes_filepath, "r") as phenotypes_file:

        data = json.load(phenotypes_file)
        assert len(data) == 2
        assert data[0]["phenocode"] == "DUMMY_COM"

    # ======== Testing top_hits ========

    run_top_hits([])

    top_hits_filepath = get_filepath("top-hits")
    top_hits_1k_filepath = get_filepath("top-hits-1k")
    top_hits_tsv = get_filepath("top-hits-tsv")

    assert Path(top_hits_filepath).exists()
    assert Path(top_hits_1k_filepath).exists()
    assert Path(top_hits_tsv).exists()

    for filepath in [top_hits_filepath, top_hits_1k_filepath]:
        with open(filepath, "r") as f:
            data = json.load(f)

            top_hit = data[0]

            assert top_hit["phenostring"] == "dummy"
            assert top_hit["pos"] == 44908822
            assert top_hit["pval"] == 2.7e-69

    # ======== Testing best_of_pheno ========

    run_best_of_pheno([])

    best_of_pheno_filepath = get_pheno_filepath(
        "best_of_pheno", dummy_phenocode)

    assert Path(best_of_pheno_filepath).exists()

    best_of_pheno_interaction_filepath = get_pheno_filepath(
        "best_of_pheno", dummy_interaction_phenocode)

    assert Path(best_of_pheno_interaction_filepath).exists()

    # ======== Testing autocomplete ========
    AutocompleteLoading()

    autocomplete_db_filepath = get_filepath(
        "autocomplete_db")

    assert Path(autocomplete_db_filepath).exists()

    autocomplete_db = sqlite3.connect(autocomplete_db_filepath)
    cur = autocomplete_db.cursor()

    cur.execute("SELECT * FROM genes")
    gene = cur.fetchone()
    assert gene == ("APOE", "19", 44905791, 44909393)

    cur.execute("SELECT * FROM phenotypes")
    phenotype = cur.fetchone()
    assert phenotype == ("DUMMY_COM", "dummy")

    cur.execute("SELECT rsid, variant_id, chrom, pos FROM variants")
    variant = cur.fetchone()
    assert variant == ("rs7412", "19-44908822-C-T", "19", 44908822)

    # ======== Testing process_assoc_files ========
    run_process_assoc_files([])
    assert True

# ==================== TEST APPEND INGEST ====================


# def _simulate_first_time_ingest():

#     summary_stat = dummy_summary_stats()
#     manifest_file = dummy_manifest_file(summary_stat)

#     run_phenolist([
#         "import-phenolist",
#         manifest_file,
#         "-f",
#         get_filepath("phenolist", must_exist=False)
#     ])

#     run_parse_input_files([])

#     run_sites([])

#     gene_aliases_fp = dummy_gene_aliases()
#     dummy_rsids_filepath = dummy_rsids()

#     run_add_rsids([])

#     dummy_genes()

#     run_add_genes([])
#     run_make_cpras_rsids_sqlite3([])
#     run_augment_phenos([])
#     run_matrix([])

#     run_gather_pvalues_for_each_gene([])
#     run_manhattan([])
#     run_qq([])
#     run_phenotypes([])
#     run_top_hits([])
#     run_best_of_pheno([])

#     AutocompleteLoading()


def test_append_ingest(use_tmp_path) -> None:
    """
    Testing an append ingest.

    This will run the entire ingest process with a new dummy phenotype (DUMMY_2_COM).

    """

    print("==================== TEST APPEND INGEST ====================")

    # Simulating first time ingest here
    simulate_first_time_ingest()
    AutocompleteLoading()

    summary_stat_2 = dummy_summary_stats_2()
    manifest_file_2 = dummy_manifest_file_2(summary_stat_2)

    # ======== Testing phenolist ========
    run_phenolist([
        "import-phenolist",
        manifest_file_2,
        "-f",
        get_filepath("phenolist", must_exist=False)
    ])

    phenolist_fp = get_filepath("phenolist")

    # asserting it contains summary_stat as assoc_file
    with open(phenolist_fp, "r") as f:
        data = json.load(f)
        assert data[0]["assoc_files"][0] == summary_stat_2

    dummy_phenocode = get_phenocode_with_suffixes(data[0])
    assert dummy_phenocode == "DUMMY_2_COM.all.both"

    dummy_interaction_phenocode = get_phenocode_with_suffixes(data[1])
    assert dummy_interaction_phenocode == "DUMMY_2_COM.interaction-sex.all.both"

    # Making sure Backup worked
    backups_phenolist = get_generated_path("backups/")
    assert len(os.listdir(backups_phenolist)) == 1

    # ======== Testing parseinputfile ========
    run_parse_input_files([])

    dummy_parsed_fp = get_pheno_filepath("parsed", dummy_phenocode)
    assert Path(dummy_parsed_fp).exists()

    dummy_interaction_parsed_fp = get_pheno_filepath(
        "parsed", dummy_interaction_phenocode)
    assert Path(dummy_interaction_parsed_fp).exists()

    # === Testing sites ===
    run_sites([])

    uanno_fp = get_filepath("unanno")

    assert Path(uanno_fp).exists()

    # Making sure that there are now 2 sites.
    with VariantFileReader(uanno_fp) as uanno_file:

        reader = iter(uanno_file)

        variant = next(reader)

        assert variant["chrom"] == "1"
        assert variant["pos"] == 21506237
        assert variant["ref"] == "C"
        assert variant["alt"] == "T"

        variant = next(reader)

        assert variant["chrom"] == "19"
        assert variant["pos"] == 44908822
        assert variant["ref"] == "C"
        assert variant["alt"] == "T"

    # ======== Testing add_rsids ========
    run_add_rsids([])

    sites_rsids_filepath = get_filepath("sites-rsids", must_exist=False)
    assert Path(sites_rsids_filepath).exists()

    # Making sure that there are now 2 sites.
    with VariantFileReader(sites_rsids_filepath) as sites_rsids_file:

        reader = iter(sites_rsids_file)

        variant = next(reader)
        assert variant["chrom"] == "1"
        assert variant["pos"] == 21506237
        assert variant["ref"] == "C"
        assert variant["alt"] == "T"
        assert variant["rsids"] == "rs3856178"

        variant = next(reader)

        assert variant["chrom"] == "19"
        assert variant["pos"] == 44908822
        assert variant["ref"] == "C"
        assert variant["alt"] == "T"
        assert variant["rsids"] == "rs7412"

    # ======== Testing add_genes ========

    run_add_genes([])

    sites_filepath = get_filepath("sites", must_exist=False)
    assert Path(sites_filepath).exists()

    # Making sure that there are now 2 sites.
    with VariantFileReader(sites_filepath) as sites_file:

        reader = iter(sites_file)

        variant = next(reader)
        assert variant["chrom"] == "1"
        assert variant["pos"] == 21506237
        assert variant["ref"] == "C"
        assert variant["alt"] == "T"
        assert variant["rsids"] == "rs3856178"
        assert variant["nearest_genes"] == "ALPL"

        variant = next(reader)

        assert variant["chrom"] == "19"
        assert variant["pos"] == 44908822
        assert variant["ref"] == "C"
        assert variant["alt"] == "T"
        assert variant["rsids"] == "rs7412"
        assert variant["nearest_genes"] == "APOE"

    # ======== Testing make_cpras_rsids_sqlite3 ========
    run_make_cpras_rsids_sqlite3([])

    cpras_rsids_filepath = get_filepath("cpras-rsids-sqlite3")

    assert Path(cpras_rsids_filepath).exists()

    cpras_rsids_db = sqlite3.connect(cpras_rsids_filepath)
    cur = cpras_rsids_db.cursor()

    #
    cur.execute("SELECT * FROM cpras_rsids")
    cpras_rsids = cur.fetchall()

    # Making sure that there are now 2 sites.
    assert cpras_rsids[0] == ('1-21506237-C-T', 'rs3856178')
    assert cpras_rsids[1] == ('19-44908822-C-T', 'rs7412')

    # ======== Testing augment_phenos ========

    run_augment_phenos([])

    # Making new phenotype as augmented phenos.
    dummy_pheno_gz_filepath = get_pheno_filepath("pheno_gz", dummy_phenocode)
    assert Path(dummy_pheno_gz_filepath).exists()

    dummy_interaction_filepath = get_pheno_filepath(
        "interaction", dummy_interaction_phenocode)
    assert Path(dummy_interaction_filepath).exists()

    # ======== Testing matrix ========
    run_matrix([])

    stratification_paths = get_stratification_paths(
        get_phenolist_no_interaction())

    matrix_gz_stratified_filepath = get_pheno_filepath(
        "matrix-stratified", stratification_paths[0], must_exist=False
    )

    assert Path(matrix_gz_stratified_filepath).exists()
    assert Path(matrix_gz_stratified_filepath + ".tbi").exists()

    # Making sure that matrix now contains both dummy phenos
    assert MatrixReader(matrix_gz_stratified_filepath).get_phenocodes()[0] == \
        "DUMMY_COM.all.both"
    assert MatrixReader(matrix_gz_stratified_filepath).get_phenocodes()[1] == \
        "DUMMY_2_COM.all.both"

    # Making sure old matrix is backup
    backup_matrix = get_generated_path("backups/matrix-stratified/")
    assert len(os.listdir(backup_matrix)) == 2

    # ======== Testing gather_pvalues_for_each_gene ========
    run_gather_pvalues_for_each_gene([])

    best_phenos_by_gene_filepath = Path(get_filepath(
        "best-phenos-by-gene-sqlite3", must_exist=False))

    best_phenos_by_gene_db = sqlite3.connect(str(best_phenos_by_gene_filepath))
    cur = best_phenos_by_gene_db.cursor()
    cur.execute("SELECT * FROM best_phenos_for_each_gene")
    best_phenos_for_each_gene = {
        gene: json.loads(data)
        for gene, data in cur.fetchall()
    }

    # Making sure best pheno by gene now contains both dummy pheno
    assert "APOE" in best_phenos_for_each_gene
    assert best_phenos_for_each_gene["APOE"][0]["phenocode"] == "DUMMY_COM.all.both"
    assert best_phenos_for_each_gene["APOE"][0]["pval"] == 2.7e-69

    assert "ALPL" in best_phenos_for_each_gene
    assert best_phenos_for_each_gene["ALPL"][0]["phenocode"] == "DUMMY_2_COM.all.both"
    assert best_phenos_for_each_gene["ALPL"][0]["pval"] == 8e-09

    # ======== Testing manhattan ========
    run_manhattan([])

    manhattan_filepath = get_pheno_filepath("manhattan", dummy_phenocode)

    assert Path(manhattan_filepath).exists()

    manhattan_interaction_filepath = get_pheno_filepath(
        "manhattan", dummy_interaction_phenocode)

    assert Path(manhattan_interaction_filepath).exists()

    with open(manhattan_filepath, "r") as manhattan_file:
        data = json.load(manhattan_file)
        assert len(data["unbinned_variants"]) == 1
        variant = data["unbinned_variants"][0]
        assert variant["chrom"] == "1"
        assert variant["pos"] == 21506237
        assert variant["ref"] == "C"
        assert variant["alt"] == "T"
        assert variant["rsids"] == "rs3856178"
        assert variant["nearest_genes"] == "ALPL"
        assert variant["pval"] == 8e-09

    with open(manhattan_interaction_filepath, "r") as manhattan_interaction_file:
        data = json.load(manhattan_interaction_file)
        assert len(data["unbinned_variants"]) == 1
        variant = data["unbinned_variants"][0]
        assert variant["chrom"] == "1"
        assert variant["pos"] == 21506237
        assert variant["ref"] == "C"
        assert variant["alt"] == "T"
        assert variant["rsids"] == "rs3856178"
        assert variant["nearest_genes"] == "ALPL"
        assert variant["pval"] == 2.6e-10

    # ======== Testing qq ========

    run_qq([])

    qq_filepath = get_pheno_filepath("qq", dummy_phenocode)

    assert Path(qq_filepath).exists()

    qq_interaction_filepath = get_pheno_filepath(
        "qq", dummy_interaction_phenocode)

    assert Path(qq_interaction_filepath).exists()

    # ======== Testing phenotypes ========

    run_phenotypes([])

    phenotypes_filepath = get_filepath("phenotypes_summary", must_exist=False)
    phenotypes_tsv_filepath = get_filepath(
        "phenotypes_summary_tsv", must_exist=False)

    assert Path(phenotypes_filepath).exists()
    assert Path(phenotypes_tsv_filepath).exists()

    with open(phenotypes_filepath, "r") as phenotypes_file:

        data = json.load(phenotypes_file)

        phenocodes = [d["phenocode"] for d in data]

        assert "DUMMY_COM" in phenocodes
        assert "DUMMY_2_COM" in phenocodes

    # ======== Testing top_hits ========

    run_top_hits([])

    top_hits_filepath = get_filepath("top-hits")
    top_hits_1k_filepath = get_filepath("top-hits-1k")
    top_hits_tsv = get_filepath("top-hits-tsv")

    assert Path(top_hits_filepath).exists()
    assert Path(top_hits_1k_filepath).exists()
    assert Path(top_hits_tsv).exists()

    for filepath in [top_hits_filepath, top_hits_1k_filepath]:
        with open(filepath, "r") as f:
            data = json.load(f)

            top_hits = {
                top_hit["phenostring"]: top_hit for top_hit in data
            }

            assert "dummy" in top_hits
            assert top_hits["dummy"]["pval"] == 1.1e-08

            assert "dummy_2" in top_hits
            assert top_hits["dummy_2"]["pval"] == 8e-09

    # ======== Testing best_of_pheno ========

    run_best_of_pheno([])

    best_of_pheno_filepath = get_pheno_filepath(
        "best_of_pheno", dummy_phenocode)

    assert Path(best_of_pheno_filepath).exists()

    best_of_pheno_interaction_filepath = get_pheno_filepath(
        "best_of_pheno", dummy_interaction_phenocode)

    assert Path(best_of_pheno_interaction_filepath).exists()

    # ======== Testing autocomplete ========
    AutocompleteLoading()

    autocomplete_db_filepath = get_filepath(
        "autocomplete_db")

    assert Path(autocomplete_db_filepath).exists()

    autocomplete_db = sqlite3.connect(autocomplete_db_filepath)
    cur = autocomplete_db.cursor()

    cur.execute("SELECT * FROM genes")
    genes = {
        row[0]: row
        for row in cur.fetchall()
    }

    assert genes["APOE"] == ("APOE", "19", 44905791, 44909393)
    assert genes["ALPL"] == ("ALPL", "1", 21509397, 21578410)

    cur.execute("SELECT * FROM phenotypes")
    phenotypes = {
        row[0]: row
        for row in cur.fetchall()
    }
    assert phenotypes["DUMMY_COM"] == ("DUMMY_COM", "dummy")
    assert phenotypes["DUMMY_2_COM"] == ("DUMMY_2_COM", "dummy_2")

    cur.execute("SELECT rsid, variant_id, chrom, pos FROM variants")
    variants = {
        row[0]: row
        for row in cur.fetchall()
    }

    assert variants["rs7412"] == ("rs7412", "19-44908822-C-T", "19", 44908822)
    assert variants["rs3856178"] == (
        "rs3856178", "1-21506237-C-T", "1", 21506237)

    # Checking that backups were properly made
    backup_sites = get_generated_path("backups/sites/")
    assert len(os.listdir(backup_sites)) == 6

    backup_root = get_generated_path("backups/")
    files = [f for f in os.listdir(backup_root)
             if os.path.isfile(os.path.join(backup_root, f))]
    assert len(files) == 7

    # ======== Testing process_assoc_files ========
    # looking at logs, nothing is being reprocessed
    run_process_assoc_files([])
    assert True
