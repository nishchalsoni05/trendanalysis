import duckdb
import pandas as pd
import os

data_dir = r"c:\Users\Nishchal Soni\Downloads\uidai\code\processed\parquet"
files = [
    "trend_typology.parquet",
    "biometric.parquet",
    "demographic.parquet",
    "enrolment.parquet"
]

for f in files:
    path = os.path.join(data_dir, f)
    if os.path.exists(path):
        print(f"--- {f} ---")
        try:
            rel = duckdb.read_parquet(path)
            cols = rel.columns
            print(f"Columns ({len(cols)}):")
            for c in cols:
                print(f"  - {c}")
            
            print("Row Count:", rel.count("1").fetchone()[0])
            print("First 2 rows:")
            print(rel.limit(2).df().to_string()) 
            print("\n")
        except Exception as e:
            print(f"Error reading {f}: {e}")
