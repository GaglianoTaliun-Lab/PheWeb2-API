import gzip
import os
from flask import current_app
import numpy as np
import sqlite3
import csv
from functools import lru_cache
import tqdm

class VariantLoading:
    def __init__(self, file_path):
        self.variants = {}
        self.variant_coordinates = np.array([])
        self.variant_info = []
        self.rsid_coordinates = np.array([])
        self.file_path = file_path

        self.db_path = os.path.join(file_path, "variants.db")
        self.load_or_create_variant_db(self.db_path)
    
    def load_or_create_variant_db(self, file_path):
        
        db_path = self.db_path
        
        if os.path.exists(db_path):
            print(f"DEBUG: Found existing database at {db_path}, skipping creation.")
            return

        print(f"DEBUG: Creating new database at {db_path}")
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
                variant_id TEXT
            )
            """)

            tsv_path = os.path.join(file_path, "sites.tsv")
            print(f"DEBUG: Loading data from {tsv_path}")
            rows = []
            with gzip.open(tsv_path, "rt") as tsvfile:
                reader = csv.DictReader(tsvfile, delimiter="\t")
                for row in tqdm.tqdm(reader, desc="Loading TSV"):
                    chrom = row["chrom"]
                    pos = row["pos"]
                    ref = row["ref"]
                    alt = row["alt"]
                    rsid = row["rsids"].split(",")[0] if row["rsids"] else None
                    variant_id = f"{chrom}-{pos}-{ref}-{alt}"
                    rows.append((rsid, variant_id))

            print(f"DEBUG: Inserting {len(rows)} rows into database")
            print(f"DEBUG: Example row: {rows[0]}")

            batch_size = 1_000_000
            cur.execute("BEGIN TRANSACTION")
            for i in tqdm.tqdm(range(0, len(rows), batch_size), desc="Inserting data"):
                batch = rows[i:i+batch_size]
                cur.executemany(
                    "INSERT INTO variants (rsid, variant_id) VALUES (?, ?)", batch
                )
            conn.commit()

            print("DEBUG: Creating indexes...")
            cur.execute("CREATE INDEX idx_rsid ON variants(rsid)")
            cur.execute("CREATE INDEX idx_variant_id ON variants(variant_id)")
            conn.commit()

            print(f"DEBUG: Database creation complete. Entries loaded.")

        except Exception as e:
            print(f"DEBUG: Error inserting data: {e}")
            conn.rollback()
            raise e
        finally:
            conn.close()

    
    @lru_cache(maxsize=1000)
    def query_variants(self, prefix, max_results=4):
        db_path = self.db_path
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        try:
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
            


    
    def get_variants(self):
        return self.variants
