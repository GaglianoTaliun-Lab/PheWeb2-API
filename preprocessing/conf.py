# TODO: standardize on `def lookup_{key}(): return overrides[key]`?

from .utils import PheWebError, load_module_from_filepath
from . import parse_utils

import os
import boltons.fileutils
from typing import Optional, Any, Dict, Tuple, List, Set


# All state lives in this dictionary.
# PheWeb2  should run fine when this is empty.
# Modify with `set_override(key,value)`.
overrides: Dict[str, Any] = {}


replacements = {
    "minimum_maf": "assoc_min_maf",
    "cache": "cache_dir",
    "limit_num_variants": "debugging_limit_num_variants",
    "aliases": "field_aliases",
}


def set_override(key: str, value: Any) -> None:
    if key in replacements:
        key = replacements[key]
        # raise PheWebError("Use `{}` instead of `{}`.".format(replacements[key], key))
    if key == "download_pheno_sumstats" and value == "secret":
        overrides["secret_download_pheno_sumstats"] = True
    if key == "download_top_hits" and value == "hide":
        overrides["show_download_top_hits_button"] = False
    if key == "download_phenotypes" and value == "hide":
        overrides["show_download_phenotypes_button"] = False
    elif key == "login":
        if not isinstance(value, dict):
            raise Exception(value)
        overrides["login"] = True
        overrides["login_GOOGLE_LOGIN_CLIENT_ID"] = value["GOOGLE_LOGIN_CLIENT_ID"]
        overrides["login_GOOGLE_LOGIN_CLIENT_SECRET"] = value[
            "GOOGLE_LOGIN_CLIENT_SECRET"
        ]
        overrides["login_allowlist"] = [
            email.lower() for email in value.get("whitelist", [])
        ]
    elif key in [
        "extra_per_variant_fields",
        "extra_per_assoc_fields",
        "extra_per_pheno_fields",
        "null_values",
    ]:
        print("Ignoring config for {} because it's not implemented.".format(key))
        # raise PheWebError("parse_utils customization isn't implemented yet.")
    elif key == "FIELD_ALIASES":
        if not isinstance(value, dict):
            raise PheWebError("FIELD_ALIASES should be dict, not {!r}".format(value))
        for alias, field_name in value.items():
            if not isinstance(alias, str):
                raise PheWebError("Alias {!r} should be str.".format(alias))
            if field_name not in parse_utils.fields:
                raise PheWebError(
                    "The name {!r} (for alias {!r}) isn't a real field.  Add it or use one of {}.".format(
                        field_name, alias, list(parse_utils.fields)
                    )
                )
        value = {
            (alias if alias.startswith("file://") else alias.lower()):
            (field_name if alias.startswith("file://") else field_name.lower())
            for alias, field_name in value.items()
        }
        overrides[key] = {**parse_utils.default_field_aliases, **value}
    elif key == "ASSOC_TEST_NAME":
        if not isinstance(value, list):
            raise PheWebError("ASSOC_TEST_NAME should be list, not {!r}".format(value))
        for test_name in value:
            if not isinstance(test_name, str):
                raise PheWebError("Test name {!r} should be str.".format(test_name))
        overrides[key] = set(value)
    else:
        overrides[key] = value


def load_overrides_from_file(filepath: str) -> None:
    if not os.path.isfile(filepath):
        raise PheWebError("Cannot load config from non-existent {!r}".format(filepath))
    try:
        module = load_module_from_filepath("config", filepath)
    except Exception:
        raise PheWebError("Failed running {!r}".format(filepath))
    for key in dir(module):
        if not key.startswith("_"):
            set_override(key, getattr(module, key))


# Utilities
def _mkdir_and_check_readable(dirpath: str) -> bool:
    if not os.path.isdir(dirpath):
        try:
            boltons.fileutils.mkdir_p(dirpath)
        except PermissionError:
            return False
    return _is_readable(dirpath)


def _is_readable(filepath: str) -> bool:
    return os.access(filepath, os.R_OK)


def _check_overrides_type(key: str, value_type: type) -> None:
    if key in overrides and not isinstance(overrides[key], value_type):
        raise PheWebError(
            "configuration for {} must be of type {}, but {!r} is of type {}".format(
                key, value_type, overrides[key], type(overrides[key])
            )
        )


def _get_config_optional_str(key: str) -> Optional[str]:
    _check_overrides_type(key, str)
    return overrides.get(key, None)


def _get_config_str(key: str, default: Optional[str] = None) -> str:
    _check_overrides_type(key, str)
    if default is None and key not in overrides:
        raise PheWebError("overrides is missing required config for {!r}".format(key))
    return overrides[key] if default is None else overrides.get(key, default)


def _get_config_optional_int(key: str) -> Optional[int]:
    _check_overrides_type(key, int)
    return overrides.get(key, None)


def _get_config_int(key: str, default: int) -> int:
    _check_overrides_type(key, int)
    return overrides.get(key, default)


def _get_config_optional_float(key: str) -> Optional[float]:
    _check_overrides_type(key, float)
    return overrides.get(key, None)


def _get_config_float(key: str, default: float) -> float:
    _check_overrides_type(key, float)
    return overrides.get(key, default)


def _get_config_bool(key: str, default: bool) -> bool:
    _check_overrides_type(key, bool)
    return overrides.get(key, default)


# Core config
def get_pheweb_data_dir() -> str:
    if 'PHEWEB_DATA_DIR' in os.environ:
        return os.path.abspath(os.environ['PHEWEBD_DATA_DIR'])
    else:
        return _get_config_str("PHEWEB_DATA_DIR", os.path.join(get_pheweb_base_dir(), "generated-by-pheweb"))


def get_pheweb_base_dir() -> str:
    if "PHEWEB_BASE_DIR" in os.environ:
        base_dir = os.environ["PHEWEB_BASE_DIR"]
    else:
        base_dir = _get_config_str("PHEWEB_BASE_DIR", os.path.curdir)
    base_dir = os.path.abspath(base_dir)
    
    if not _mkdir_and_check_readable(base_dir):
        raise PheWebError(
            "PheWeb cannot use PHEWEB_BASE_DIR {!r}, because it either can't create it or can't read it.".format(
                base_dir
            )
        )
    return base_dir


def get_cache_dir() -> Optional[str]:
    key = "cache_dir"
    if not overrides.get(key):
        return None
    cache_dir = _get_config_str(key, "~/.pheweb/cache")
    cache_dir = os.path.abspath(os.path.expanduser(cache_dir))
    if not _mkdir_and_check_readable(cache_dir):
        print(
            "Warning: caching is disabled because PheWeb either can't create or can't read {!r}.".format(
                cache_dir
            )
        )
        overrides[key] = False
        return None
    return cache_dir


## Debugging config
def is_debug_mode() -> bool:
    return "PHEWEB_DEBUG" in os.environ or _get_config_bool("debug", False)


def get_debugging_limit_num_variants() -> Optional[int]:
    return _get_config_optional_int("debugging_limit_num_variants")


def is_allowed_to_download() -> bool:
    return not _get_config_bool("disallow_downloads", False)


## Loading config
def get_num_procs(cmd: Optional[str] = None) -> int:
    import multiprocessing

    key = "num_procs"
    try:
        return int(overrides[key][cmd])
    except Exception:
        pass
    try:
        return int(overrides[key]["*"])
    except Exception:
        pass
    try:
        return int(overrides[key])
    except Exception:
        pass
    n_cpus = multiprocessing.cpu_count()
    return 1 if n_cpus == 1 else int(n_cpus * 3 / 4)


# Configuration for the external databases
def get_hg_build_number() -> int:
    ret = _get_config_int("HG_BUILD_NUMBER", 19)
    if ret not in [19, 38]:
        raise PheWebError(
            "hg_build_number must be either 19 or 38, not {!r}".format(ret)
        )
    return ret


def get_grch_build_number() -> int:
    hg = get_hg_build_number()
    return hg if hg >= 38 else 18 + hg


def get_gencode_version() -> int:
    return _get_config_int("GENCODE_VERSION", 47)


def get_dbsnp_version() -> int:
    return _get_config_int("DBSNP_VERSION", 157)


## Configuration for parsing/ingesting GWAS files
def has_stratifications() -> bool:
    return _get_config_bool("ENABLE_STRATIFICATIONS", True)


def get_assoc_test_name() -> Set[str]:
    return overrides.get("ASSOC_TEST_NAME", {"ADD"})


def get_assoc_min_maf() -> float:
    return _get_config_float("ASSOC_MIN_MAF", 0)


def get_interaction_test_name() -> str:
    return _get_config_str("INTERACTION_TEST_NAME", "ADD-INT_SNPxVAR")


def get_interaction_min_maf() -> float:
    return _get_config_optional_float("INTERACTION_MIN_MAF")


def get_interaction_min_mac() -> int:
    return _get_config_optional_int("INTERACTION_MIN_MAC")


def pval_is_neglog10() -> bool:
    return _get_config_bool("PVAL_IS_NEGLOG10", False)


def get_min_imp_quality() -> float:
    return _get_config_float("MIN_IMP_QUALITY", 0.3)


def get_field_aliases() -> Dict[str, str]:
    return overrides.get("FIELD_ALIASES", parse_utils.default_field_aliases)


## Manhattan / top-hits / top-loci config
def get_within_pheno_mask_around_peak() -> int:
    return _get_config_int("within_pheno_mask_around_peak", 500_000)


def get_between_pheno_mask_around_peak() -> int:
    return _get_config_int("between_pheno_mask_around_peak", 1_000_000)


def get_manhattan_num_unbinned() -> int:
    return _get_config_int("manhattan_num_unbinned", 500)


def get_manhattan_peak_max_count() -> int:
    return _get_config_int("manhattan_peak_max_count", 500)


def get_manhattan_peak_pval_threshold() -> float:
    return _get_config_float("manhattan_peak_pval_threshold", 1e-6)


def get_manhattan_peak_sprawl_dist() -> int:
    return _get_config_int("manhattan_peak_sprawl_dist", 200_000)


def get_manhattan_peak_variant_counting_pval_threshold() -> float:
    return _get_config_float("manhattan_peak_variant_counting_pval_threshold", 5e-8)


def get_top_hits_pval_cutoff() -> float:
    return _get_config_float("top_hits_pval_cutoff", 1e-6)


## Pheno correlation config
def should_show_correlations() -> bool:
    return _get_config_bool("show_correlations", False)


def get_pheno_correlations_pvalue_threshold() -> float:
    return _get_config_float("pheno_correlations_pvalue_threshold", 0.05)


## Serving config
def get_lzjs_version() -> str:
    return _get_config_str("lzjs_version", "0.13.4")


def should_allow_variant_json_cors() -> bool:
    return _get_config_bool("allow_variant_json_cors", True)


def get_urlprefix() -> str:
    return _get_config_str("urlprefix", "").rstrip("/")


def get_custom_templates_dir() -> Optional[str]:
    key = "custom_templates"
    custom_templates_dir = _get_config_str(key, "custom_templates")
    custom_templates_dir = os.path.abspath(os.path.expanduser(custom_templates_dir))
    if not _is_readable(custom_templates_dir):
        return None
    return custom_templates_dir


def is_login_required() -> bool:
    return bool(overrides.get("login"))


def get_login_google_id_and_secret() -> Tuple[str, str]:
    if not overrides.get("login"):
        raise PheWebError("Missing login config")
    return (
        _get_config_str("login_GOOGLE_LOGIN_CLIENT_ID"),
        _get_config_str("login_GOOGLE_LOGIN_CLIENT_SECRET"),
    )


def get_login_allowlist() -> List[str]:
    key = "login_allowlist"
    _check_overrides_type(key, list)
    return overrides.get(key, [])  # type: ignore


def get_secret_key() -> str:
    return _get_config_str("SECRET_KEY", "nonsecret key")


def should_show_download_top_hits_button() -> bool:
    return _get_config_bool("show_download_top_hits_button", True)


def should_show_download_phenotypes_button() -> bool:
    return _get_config_bool("show_download_phenotypes_button", True)


def is_secret_download_pheno_sumstats() -> bool:
    return _get_config_bool("secret_download_pheno_sumstats", False)


def get_google_analytics_id() -> Optional[str]:
    return _get_config_optional_str("GOOGLE_ANALYTICS_TRACKING_ID")


def get_sentry_id() -> Optional[str]:
    return _get_config_optional_str("SENTRY_DSN")


def should_show_manhattan_filter_button() -> bool:
    return _get_config_bool("show_manhattan_filter_button", False)


def should_show_manhattan_filter_consequence() -> bool:
    return _get_config_bool("show_manhattan_filter_consequence", False)


