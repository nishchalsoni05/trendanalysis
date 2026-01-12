"""
Script to explore the UIDAI dataset structure - outputs to JSON.
"""
import csv
import os
import json

DATA_ROOT = "data"

def read_csv_sample(filepath, num_rows=3):
    """Read header and sample rows from a CSV file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = []
        for i, row in enumerate(reader):
            if i >= num_rows + 1:
                break
            rows.append(row)
    return rows

def main():
    result = {}
    
    for folder in os.listdir(DATA_ROOT):
        folder_path = os.path.join(DATA_ROOT, folder)
        if os.path.isdir(folder_path):
            csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
            if csv_files:
                first_file = os.path.join(folder_path, sorted(csv_files)[0])
                rows = read_csv_sample(first_file, 3)
                
                if rows:
                    result[folder] = {
                        "sample_file": csv_files[0],
                        "total_files": len(csv_files),
                        "columns": rows[0],
                        "column_count": len(rows[0]),
                        "sample_rows": rows[1:]
                    }
    
    # Write to JSON file
    with open('data_schema.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print("Schema written to data_schema.json")

if __name__ == "__main__":
    main()
