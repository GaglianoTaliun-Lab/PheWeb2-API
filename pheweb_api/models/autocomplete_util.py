import gzip
import os
# from flask import current_app
import sqlite3
import csv
from functools import lru_cache
import tqdm
from .models import create_phenotypes_list, create_genes
from flask import g
from ..conf import is_debug_mode, get_pheweb_data_dir


class GenesServiceNotAvailable(Exception):
    pass

# def get_genes_service():
#     if "genes" not in g:
#         g.genes = create_genes()
#         if g.genes is None:
#             raise GenesServiceNotAvailable(
#                 "Could not create gene service. Check if data path (named generated-by-pheweb/ by default) is correctly configured in .env or config.py."
#             )
#     return g.genes


# class PhenotypeServiceNotAvailable(Exception):
#     pass


# def get_pheno_service():
#     if "pheno" not in g:
#         g.pheno = create_phenotypes_list()
#         if g.pheno is None:
#             raise PhenotypeServiceNotAvailable(
#                 "Could not create phenotype service. Check if data path (named generated-by-pheweb/ by default) is correctly configured in .env or config.py."
#             )
#     return g.pheno


class AutocompleteLoading:
    def __init__(self):
        self.variants = {}
        self.file_path = os.path.join(get_pheweb_data_dir(), "sites")
        self.db_path = os.path.join(self.file_path, "autocomplete.db")
        print(f"DEBUG: db_path: {self.db_path}")
        self.create_table()
        self._load_to_memory()

        
    def _load_to_memory(self):
        file_connection = sqlite3.connect(self.db_path)
        mem_connection = sqlite3.connect(":memory:", check_same_thread=False)
        file_connection.backup(mem_connection)
        file_connection.close()

        try:
            cur = mem_connection.cursor()
            cur.execute("SELECT COUNT(*) FROM variants")
            count = cur.fetchone()[0]
            if is_debug_mode(): print(f"DEBUG: {count} variant records loaded into memory")
            # cur.execute("SELECT rsid, variant_id FROM variants LIMIT 5")
            # sample_rows = cur.fetchall()
            # print(f"DEBUG: Sample rsids in DB: {sample_rows}")

            cur.execute("SELECT COUNT(*) FROM genes")
            count = cur.fetchone()[0]
            if is_debug_mode(): print(f"DEBUG: {count} gene records loaded into memory")

            cur.execute("SELECT COUNT(*) FROM phenotypes")
            count = cur.fetchone()[0]
            if is_debug_mode(): print(f"DEBUG: {count} phenotype records loaded into memory")
            
        except Exception as e:
            print("DEBUG: Failed to query memory DB:", e)

        self.connection = mem_connection
    
    def table_exists(self, cur, table_name):
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return cur.fetchone() is not None
    
    def create_table(self):
        if os.path.exists(self.db_path):
            if is_debug_mode(): print(f"DEBUG: Found existing database at {self.db_path}")
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            if not self.table_exists(cur, "variants"):
                if is_debug_mode(): print(f"DEBUG: Creating variants table")
                self.create_autocomplete_db_variants_table()

            if not self.table_exists(cur, "genes"):
                if is_debug_mode(): print(f"DEBUG: Creating genes table")
                self.create_autocomplete_db_genes_table()

            if not self.table_exists(cur, "phenotypes"):
                if is_debug_mode(): print(f"DEBUG: Creating phenotypes table")
                self.create_autocomplete_db_phenotypes_table()

            if self.table_exists(cur, "phenotypes") and not self.table_exists(cur, "phenotypes_fts"):
                if is_debug_mode(): print(f"DEBUG: Creating phenotypes_fts virtual table")
                cur.execute("""
                    CREATE VIRTUAL TABLE phenotypes_fts USING fts5(
                        phenocode,
                        phenostring,
                        content=phenotypes,
                        content_rowid=rowid
                    )
                """)
                cur.execute("INSERT INTO phenotypes_fts(phenotypes_fts) VALUES ('rebuild')")
                conn.commit()
                if is_debug_mode(): print("DEBUG: phenotypes_fts virtual table created and rebuilt.")
           
            conn.close()
            if is_debug_mode(): print(f"DEBUG: Database creation complete. Entries loaded.")
            return
        else:
            if is_debug_mode(): print(f"DEBUG: Creating new database at {self.db_path}")
            self.create_autocomplete_db_variants_table()
            self.create_autocomplete_db_genes_table()
            self.create_autocomplete_db_phenotypes_table()
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            if is_debug_mode(): print("DEBUG: Creating phenotypes_fts virtual table...")
            cur.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS phenotypes_fts USING fts5(
                    phenocode,
                    phenostring,
                    content='phenotypes',
                    content_rowid='rowid'
                )
            """)
            cur.execute("INSERT INTO phenotypes_fts(phenotypes_fts) VALUES ('rebuild')")
            conn.commit()
            conn.close()
            if is_debug_mode(): print("DEBUG: phenotypes_fts virtual table created and rebuilt.")
        
    
    def create_autocomplete_db_variants_table(self):
        
        db_path = self.db_path

        # if is_debug_mode(): print(f"DEBUG: Creating new database at {db_path}")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        try:
            cur.execute("PRAGMA journal_mode = OFF")
            cur.execute("PRAGMA synchronous = OFF")
            cur.execute("PRAGMA cache_size = 1000000")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS variants (
                    id INTEGER PRIMARY KEY,
                    rsid TEXT,
                    variant_id TEXT,
                    chrom TEXT,
                    pos INTEGER
                )
            """)

            tsv_path = os.path.join(self.file_path, "sites.tsv")
            if is_debug_mode(): print(f"DEBUG: Loading data from {tsv_path}")
            rows = []
            batch_size = 1_000_000
            with gzip.open(tsv_path, "rt") as tsvfile:
                reader = csv.DictReader(tsvfile, delimiter="\t")
                for row in tqdm.tqdm(reader, desc="Loading TSV"):
                    chrom = row["chrom"]
                    pos = row["pos"]
                    ref = row["ref"]
                    alt = row["alt"]
                    rsid = row["rsids"].split(",")[0] if row["rsids"] else None
                    variant_id = f"{chrom}-{pos}-{ref}-{alt}"
                    rows.append((rsid, variant_id, chrom, int(pos)))
                    if len(rows) >= batch_size:
                        if is_debug_mode(): print(f"\nDEBUG: Inserting {len(rows)} rows into database")
                        if is_debug_mode(): print(f"DEBUG: Example row: {rows[0]}")
                        cur.execute("BEGIN TRANSACTION")
                        cur.executemany(
                            "INSERT INTO variants (rsid, variant_id, chrom, pos) VALUES (?, ?, ?, ?)", rows
                        )
                        rows = []
                        conn.commit()
                if len(rows) > 0:
                    if is_debug_mode(): print(f"DEBUG: Inserting {len(rows)} rows into database")
                    if is_debug_mode(): print(f"DEBUG: Example row: {rows[0]}")
                    cur.execute("BEGIN TRANSACTION")
                    cur.executemany(
                        "INSERT INTO variants (rsid, variant_id, chrom, pos) VALUES (?, ?, ?, ?)", rows
                    )
                    rows = []
                    conn.commit()

            if is_debug_mode(): print("DEBUG: Creating indexes for rsid and variant_id...")
            cur.execute("CREATE INDEX idx_variant_id ON variants(variant_id)")
            cur.execute("CREATE INDEX idx_rsid ON variants(rsid)")
            cur.execute("CREATE INDEX idx_chrom ON variants(chrom)")
            cur.execute("CREATE INDEX idx_pos ON variants(pos)")
            # cur.execute("CREATE INDEX idx_pos_str ON variants(pos_str)")
            conn.commit()

            if is_debug_mode(): print(f"DEBUG: Database creation complete. Entries loaded.")

        except Exception as e:
            print(f"DEBUG: Error inserting data: {e}")
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    
    def create_autocomplete_db_genes_table(self):
        db_path = self.db_path
        # genes_service = get_genes_service()
        # gene_dict = genes_service.get_all_genes()
        gene_dict = create_genes().get_all_genes()
        
        if gene_dict is None:
            raise Exception("genes cannot be retrieved")
            # raise GenesServiceNotAvailable(
            #     "Could not create gene service. Check if data path (named generated-by-pheweb/ by default) is correctly configured in .env or config.py."
            # )
        
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS genes (
                    gene_id TEXT PRIMARY KEY,
                    chrom TEXT,
                    start INTEGER,
                    stop INTEGER
                )
            """)

            rows = [
                (gene, val["chrom"], val["start"], val["stop"])
                for gene, val in gene_dict.items()
            ]
            cur.execute("BEGIN TRANSACTION")
            cur.executemany("INSERT INTO genes (gene_id, chrom, start, stop) VALUES (?, ?, ?, ?)", rows)
            conn.commit()
            if is_debug_mode(): print(f"DEBUG: Genes table creation complete. {len(rows)} entries loaded.")
        except Exception as e:
            print(f"DEBUG: Error inserting data: {e}")
            conn.rollback()
            raise e
        finally:
            conn.close()

    def create_autocomplete_db_phenotypes_table(self):
        db_path = self.db_path
        
        # pheno_service = get_pheno_service()
        # pheno_dict = pheno_service.get_all_pheno_names()
        pheno_dict = create_phenotypes_list().get_all_pheno_names()
        if pheno_dict is None:
            raise Exception("phenotypes cannot be retrieved")
            # raise PhenotypeServiceNotAvailable(
            #     "Could not create phenotype service. Check if data path (named generated-by-pheweb/ by default) is correctly configured in .env or config.py."
            # )
        
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS phenotypes (
                    phenocode TEXT PRIMARY KEY,
                    phenostring TEXT
                )
            """)

            rows = [
                (phenocode, val["phenostring"])
                for phenocode, val in pheno_dict.items()
            ]
            cur.execute("BEGIN TRANSACTION")
            cur.executemany("INSERT INTO phenotypes (phenocode, phenostring) VALUES (?, ?)", rows)
            conn.commit()
            if is_debug_mode(): print(f"DEBUG: Phenotypes table creation complete. {len(rows)} entries loaded.")

            if is_debug_mode(): print("DEBUG: Creating indexes for phenostring...")
            cur.execute("CREATE INDEX idx_phenostring ON phenotypes(phenostring)")
            conn.commit()

            if is_debug_mode(): print(f"DEBUG: Database creation complete. Entries loaded.")

        except Exception as e:
            print(f"DEBUG: Error inserting data: {e}")
            conn.rollback()
            raise e
        finally:
            conn.close()




    # @lru_cache(maxsize=1000)
    def query_variants(self, prefix: str, chrom: str = None, pos: int = None, max_results=4):
        # db_path = self.db_path
        # conn = sqlite3.connect(db_path)
        # cur = conn.cursor()
        # print(f"DEBUG: query_variants called")
        # print(f"DEBUG: self.connection = {self.connection}")
        try:
            cur = self.connection.cursor()
            # print(f"DEBUG: cursor created")
            cur.execute("SELECT rsid, variant_id FROM variants LIMIT 1")
            sample_rows = cur.fetchall()
            if is_debug_mode(): print(f"DEBUG: Sample rsids in DB: {sample_rows}")
        except Exception as e:
            print(f"DEBUG: Error querying variants: {e}")
            raise e
        
        try:
            if is_debug_mode(): print(f"DEBUG: chrom: {chrom}, pos: {pos}")

            if chrom and pos:
                pos_window = 10
                pos_min = int(pos) - pos_window
                pos_max = int(pos) + pos_window
                exact = prefix
                like_pattern = prefix + "%"
                cur.execute("""
                    SELECT rsid, variant_id FROM variants
                    WHERE chrom = ? and variant_id = ?
                """, (chrom, exact))
                exact_matches = cur.fetchall()
                if len(exact_matches) != 0:
                    return exact_matches
                else:
                    similar_matches = []
                    cur.execute("""
                        SELECT rsid, variant_id FROM variants
                        WHERE chrom = ? and variant_id LIKE ?
                        AND variant_id != ?
                        LIMIT ?
                    """, (chrom, like_pattern, exact, max_results))
                    similar_matches = cur.fetchall()
                    return similar_matches

            else:
                exact = prefix
                like_pattern = prefix + "%"

                cur.execute("""
                    SELECT rsid, variant_id FROM variants
                    WHERE rsid = ? OR variant_id = ?
                """, (exact, exact))
                exact_matches = cur.fetchall()
                if len(exact_matches) != 0:
                    return exact_matches
                else:
                    similar_matches = []

                    cur.execute("""
                        SELECT rsid, variant_id FROM variants
                        WHERE (rsid LIKE ? OR variant_id LIKE ?)
                        AND rsid != ?
                        AND variant_id != ?
                        LIMIT ?
                    """, (like_pattern, like_pattern, exact, exact, max_results))
                    similar_matches = cur.fetchall()

                return similar_matches

        except Exception as e:
            print(f"DEBUG: Error querying variants: {e}")
            raise e

    def query_genes(self, prefix, max_results=4):

        try:
            cur = self.connection.cursor()
        except Exception as e:
            print(f"DEBUG: Error querying variants: {e}")
            raise e
        
        try:
            exact = prefix
            like_pattern = prefix + "%"

            cur.execute("""
                SELECT gene_id, chrom, start, stop FROM genes
                WHERE gene_id = ?
            """, (exact,))
            exact_matches = cur.fetchall()
            if len(exact_matches) != 0:
                return exact_matches
            else:
                similar_matches = []

                cur.execute("""
                    SELECT gene_id, chrom, start, stop FROM genes
                    WHERE (gene_id LIKE ?)
                    AND gene_id != ?
                    LIMIT ?
                """, (like_pattern, exact, max_results))
                similar_matches = cur.fetchall()

            return similar_matches

        except Exception as e:
            print(f"DEBUG: Error querying genes: {e}")
            raise e   

    def query_phenotypes(self, prefix, max_results=4):

        try:
            cur = self.connection.cursor()
        except Exception as e:
            print(f"DEBUG: Error querying phenotypes: {e}")
            raise e

        try:
            exact = prefix
            like_pattern = "%" + prefix + "%"

            cur.execute("""
                SELECT phenocode, phenostring FROM phenotypes_fts
                WHERE phenostring = ?
            """, (exact,))
            exact_matches = cur.fetchall()
            if len(exact_matches) != 0:
                return exact_matches
            else:
                similar_matches = []

                cur.execute("""
                    SELECT phenocode, phenostring FROM phenotypes_fts
                    WHERE (phenocode LIKE ? OR phenostring LIKE ?)
                    AND phenocode != ?
                    AND phenostring != ?
                    LIMIT ?
                """, (like_pattern, like_pattern, exact, exact, max_results))
                similar_matches = cur.fetchall()
                
                search_term = prefix.strip()
                cur.execute("""
                    SELECT phenocode, phenostring
                    FROM phenotypes_fts
                    WHERE phenotypes_fts MATCH ?
                    LIMIT ?
                """, (f"phenocode:{search_term} OR phenostring:{search_term}", max_results))
                similar_matches.extend(cur.fetchall())
                if len(similar_matches) == 0:
                    return []
                else:
                    return list(set(similar_matches))


        except Exception as e:
            print(f"DEBUG: Error querying phenotypes: {e}")
            raise e
    

