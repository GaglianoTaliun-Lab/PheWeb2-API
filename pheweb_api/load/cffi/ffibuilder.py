# For reference, see <https://github.com/quinlan-lab/hts-python/blob/master/hts/htsffi.py>, even though it uses deprecated .verify()

import cffi
import os.path

cxx_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x.cpp")
with open(cxx_path) as f:
    src = f.read()

ffibuilder = cffi.FFI()
ffibuilder.set_source(
    "pheweb_api.load.cffi._x",
    src,
    source_extension=".cpp",
    extra_compile_args=["--std=c++11"],
    libraries=["z"],  # needed on Linux but not macOS
)
ffibuilder.cdef("""
const char* cffi_make_matrix(const char *sites_filepath, const char *augmented_pheno_glob, const char *matrix_filepath);
const char* cffi_append_to_matrix(const char *sites_filepath, const char **pheno_files, const size_t n_phenos, const char *old_matrix_filepath, const char *new_matrix_filepath);
""")

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)