import csv
import typing as ty
from flask import current_app

chrom_order_list = [str(i) for i in range(1, 22 + 1)] + ["X", "Y", "MT"]
chrom_order = {chrom: index for index, chrom in enumerate(chrom_order_list)}
chrom_aliases = {"23": "X", "24": "Y", "25": "MT", "M": "MT"}
for chrom in chrom_order_list:
    chrom_aliases["chr{}".format(chrom)] = chrom
for alias, chrom in list(chrom_aliases.items()):
    chrom_aliases["chr{}".format(alias)] = chrom


def get_gene_tuples_with_ensg() -> ty.Iterator[ty.Tuple[str, int, int, str, str]]:
    with open(
        # f'{current_app.config['BASE_DIR']}/resources/genes-v{37}-hg{38}.bed'
        f"{current_app.config['BASE_DIR']}/resources/genes-v{37}-hg{38}.bed"
    ) as f:  # TODO : this was flexible in the original pheweb
        for row in csv.reader(f, delimiter="\t"):
            assert row[0] in chrom_order, row[0]
            yield (row[0], int(row[1]), int(row[2]), row[3], row[4])


def get_gene_tuples() -> ty.Iterator[ty.Tuple[str, int, int, str]]:
    for chrom, start, end, genename, ensg in get_gene_tuples_with_ensg():
        yield (chrom, start, end, genename)
