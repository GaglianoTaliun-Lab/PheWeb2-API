import os
import contextlib

from ..file_utils import MatrixReader
from ..file_utils import (
    VariantFileReader,
    VariantFileWriter,
    get_filepath,
    read_maybe_gzip,
    backup_file
)


os.environ['PHEWEB_DATA_DIR'] = "/home/jordboul/scratch/PheWeb/Dev_data"

sites_filepath = "/home/jordboul/scratch/PheWeb/Dev_data/sites/sites.tsv"
matrix_filepath =  "/home/jordboul/scratch/PheWeb/Dev_data/matrix-stratified/matrix.all.both.tsv.gz"


# sites_filepath = "/home/jordboul/scratch/PheWeb/Dev_data/sites/sites.tsv"
# matrix_filepath =  "/home/jordboul/scratch/PheWeb/PheWeb2.0-API/generated-by-pheweb/matrix-stratified/matrix.all.both.tsv.gz"


matrix = MatrixReader(matrix_filepath)
vfr = VariantFileReader(sites_filepath)


# with contextlib.ExitStack() as exit_stack:

#     reader = iter(
#         exit_stack.enter_context(
#             matrix
#         )
#     )



with matrix.context() as f, vfr as vfr_c:
    it_m = iter(f)
    it_v = iter(vfr_c)
    
    i = 0

    while(it_m):
        m_next = next(it_m)
    
        # print(m_next)
        # break

        try:
            if not m_next["phenos"]["CCC_CANC_COM.all.both"]["pval"]:
                print(m_next)
        except KeyError as err:
            print("====================")
            print(i, err, print(m_next["rsids"]))
            print(m_next)
            print("====================")
        i += 1
