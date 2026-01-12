
import shutil
import tempfile
import zipfile
import tarfile
import patoolib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime
import polars as pl


class HardenedDataIngestionManager:
    """
    GOVERNMENT-GRADE DATA INGESTION ENGINE
    
    Standards:
    1. Content-Based Classification (Headers Only, No Filenames)
    2. Strict Target Paths (data/api_data_aadhar_*)
    3. Recursive Archive Extraction (ZIP/RAR/TAR)
    4. Manual Fallback Scanning (data/manual/)
    """
    
    def __init__(self, data_root: Path = None):
        """Initialize with strict production paths."""
        self.data_root = data_root or Path("data")
        self.data_root.mkdir(parents=True, exist_ok=True)
        
        # 1. Define Canonical Targets (The ONLY place validated data lives)
        self.targets = {
            "enrolment": self.data_root / "api_data_aadhar_enrolment",
            "demographic": self.data_root / "api_data_aadhar_demographic",
            "biometric": self.data_root / "api_data_aadhar_biometric"
        }
        
        for target in self.targets.values():
            target.mkdir(parents=True, exist_ok=True)
            
        # 2. Manual Fallback Source (Input Only)
        self.manual_source = self.data_root / "manual"
        self.manual_source.mkdir(parents=True, exist_ok=True)
        
        # 3. Unknown/Unclassified trash bin
        self.unknown_dir = self.data_root / "manual" / "_unknown"
        self.unknown_dir.mkdir(parents=True, exist_ok=True)
        
        # 4. Staging
        self.staging_root = self.data_root / "_staging_uploads"
        self.staging_root.mkdir(parents=True, exist_ok=True)
        
        # SCHEMA SIGNATURES (Strict Content Matching)
        self.schema_signatures = {
            "enrolment": {
                "keywords": {
                    "enrolment", "aadhaar_generated", "age_0_5", "age_5_17", "age_18_plus", 
                    "age_18_greater", "rejected", "enrolment_agency"
                }
            },
            "biometric": {
                "keywords": {
                    "biometric", "fingerprint", "iris", "face", "bio_update",
                    "bio_age_5_17", "bio_age_17_"
                }
            },
            "demographic": {
                "keywords": {
                    "demographic", "address", "mobile", "gender", "dob", "email_update",
                    "demo_age_5_17", "demo_age_17_"
                }
            }
        }
        
        self.log = []
    
    def _log(self, message: str, level: str = "INFO"):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbol = "✓" if level=="SUCCESS" else "✗" if level=="ERROR" else "ℹ"
        log_entry = f"[{timestamp}] {symbol} {message}"
        self.log.append({"msg": log_entry, "level": level})
        print(log_entry)

    def extract_archive_recursive(self, archive_path: Path, extract_to: Path) -> List[Path]:
        """
        Secure Recursive Archive Extraction.
        Supports ZIP, TAR, RAR.
        """
        self._log(f"Processing archive: {archive_path.name}", "INFO")
        
        try:
            file_ext = archive_path.suffix.lower()
            
            # Handle ZIP
            if file_ext == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
            
            # Handle TAR
            elif file_ext in ['.tar', '.gz', '.tgz', '.bz2']:
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_to)
                    
            # Handle RAR
            elif file_ext == '.rar':
                try:
                    patoolib.extract_archive(str(archive_path), outdir=str(extract_to))
                except Exception as e:
                    self._log(f"RAR Extraction Error: {e}. Ensure 7-Zip or unrar is installed.", "ERROR")
                    return []
            
            else:
                 return []
            
            self._log(f"Extracted {archive_path.name}", "SUCCESS")
            
            # RECURSION: Look for nested archives or CSVs
            discovered_csvs = []
            
            # Walk through extracted files
            for root, dirs, files in os.walk(extract_to):
                for file in files:
                    file_path = Path(root) / file
                    sub_ext = file_path.suffix.lower()
                    
                    if sub_ext in ['.zip', '.rar', '.tar', '.gz']:
                        # Nested archive -> Recurse
                        nested_extract_to = extract_to / f"nested_{file_path.stem}"
                        nested_extract_to.mkdir(exist_ok=True)
                        discovered_csvs.extend(self.extract_archive_recursive(file_path, nested_extract_to))
                    elif sub_ext == '.csv':
                        discovered_csvs.append(file_path)
            
            return discovered_csvs
        
        except Exception as e:
            self._log(f"Extraction failed for {archive_path.name}: {e}", "ERROR")
            return []

    def detect_dataset_type_by_schema(self, csv_path: Path) -> str:
        """
        Strict Header-Based Classification.
        Reads first row ONLY. Case-insensitive.
        """
        try:
            # Read header only
            df = pl.read_csv(csv_path, n_rows=0)
            columns = {col.lower().strip() for col in df.columns}
            
            # Score each schema
            scores = {}
            for dtype, rules in self.schema_signatures.items():
                keywords = rules["keywords"]
                # Count matches
                matches = len(columns.intersection(keywords))
                
                # Check for substring matches (content robustness)
                substring_matches = 0
                for col in columns:
                    for kw in keywords:
                        if kw in col:
                            substring_matches += 1
                            break
                
                scores[dtype] = matches + (substring_matches * 0.5)
            
            # Get best match
            best_type = max(scores, key=scores.get)
            best_score = scores[best_type]
            
            # Strength Threshold
            if best_score >= 1.0: 
                self._log(f"Classified {csv_path.name} -> {best_type.upper()} (Score: {best_score})", "SUCCESS")
                return best_type
            
            return "unknown"
            
        except Exception as e:
            self._log(f"Schema check failed for {csv_path.name}: {e}", "ERROR")
            return "error"

    def move_to_target(self, csv_path: Path, dataset_type: str) -> bool:
        """
        Move file to canonical data/api_data_aadhar_{type}/ location.
        """
        if dataset_type == "error": return False
        
        if dataset_type == "unknown":
            target_dir = self.unknown_dir
        else:
            target_dir = self.targets[dataset_type]
            
        target_path = target_dir / csv_path.name
        
        # De-duplication logic (append timestamp if exists)
        if target_path.exists():
            timestamp = datetime.now().strftime("%H%M%S")
            target_path = target_dir / f"{csv_path.stem}_{timestamp}.csv"
            
        try:
            shutil.copy2(str(csv_path), str(target_path))
            return True
        except Exception as e:
            self._log(f"Failed to move {csv_path.name}: {e}", "ERROR")
            return False

    def scan_and_ingest_all(self):
        """
        Universal Data Discovery (Manual Folder + Staging).
        """
        self.log = []
        self._log("STARTING DATA DISCOVERY")
        
        # 1. Clean Staging Area
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        staging_dir = self.staging_root / f"scan_{timestamp}"
        staging_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Gather all potential inputs from data/manual
            raw_candidates = []
            
            # Recursively scan manual/
            for path in self.manual_source.rglob("*"):
                if path.is_file() and "_unknown" not in str(path):
                    raw_candidates.append(path)
            
            self._log(f"Found {len(raw_candidates)} files in manual workspace")
            
            csv_candidates = []
            
            for path in raw_candidates:
                ext = path.suffix.lower()
                
                if ext in ['.zip', '.rar', '.tar', '.gz']:
                    self._log(f"Extracting Archive: {path.name}", "INFO")
                    # Extract to temp staging
                    extracted = self.extract_archive_recursive(path, staging_dir)
                    csv_candidates.extend(extracted)
                elif ext == '.csv':
                    csv_candidates.append(path)
            
            # Classify & Move
            self._log(f"Processing {len(csv_candidates)} CSV candidates...")
            success_count = 0
            
            for csv_path in csv_candidates:
                dtype = self.detect_dataset_type_by_schema(csv_path)
                if dtype != "error":
                    if self.move_to_target(csv_path, dtype):
                        success_count += 1
            
            self._log(f"Ingestion Complete. Processed {success_count} files.", "SUCCESS")
            
        except Exception as e:
            self._log(f"Scan failed: {e}", "ERROR")
            
        return self.validate_datasets()

    def validate_datasets(self) -> Dict[str, any]:
        """
        VALIDATION GATE: Checks data/api_data_aadhar_* locations.
        """
        summary = {}
        missing = []
        
        self._log("RUNNING VALIDATION GATE", "INFO")
        
        for dtype, folder in self.targets.items():
            files = list(folder.glob("*.csv"))
            count = len(files)
            
            summary[f"{dtype}_files"] = count
            
            if count == 0:
                missing.append(dtype)
                self._log(f"✗ Missing {dtype}", "ERROR")
            else:
                self._log(f"✓ {dtype.upper()}: {count} files", "SUCCESS")
                
        is_valid = len(missing) == 0
        
        if not is_valid:
             self._log("❌ Pipeline Locked: Missing required datasets", "ERROR")
        else:
             self._log("✅ Validation Passed: Pipeline Ready", "SUCCESS")

        return {
            "valid": is_valid,
            "errors": missing,
            "summary": summary
        }

    def process_upload(self, uploaded_files):
        """
        Handle UI Uploads.
        """
        self.log = [] 
        self._log("STARTING UPLOAD INGESTION")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        staging_dir = self.staging_root / timestamp
        staging_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            saved_paths = []
            for uploaded_file in uploaded_files:
                file_path = staging_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                saved_paths.append(file_path)
            
            all_csvs = []
            for file_path in saved_paths:
                ext = file_path.suffix.lower()
                if ext in ['.zip', '.rar', '.tar', '.gz']:
                    all_csvs.extend(self.extract_archive_recursive(file_path, staging_dir))
                elif ext == '.csv':
                    all_csvs.append(file_path)
                    
            if not all_csvs:
                self._log("No valid CSVs found in upload.", "ERROR")
                return self.validate_datasets()

            success_count = 0
            for csv_path in all_csvs:
                dtype = self.detect_dataset_type_by_schema(csv_path)
                if dtype != "error":
                     if self.move_to_target(csv_path, dtype):
                         success_count += 1
            
            self._log(f"Upload Complete. Organized {success_count} files.", "SUCCESS")
            
        except Exception as e:
            self._log(f"Upload Critical Error: {e}", "ERROR")
            
        return self.validate_datasets()

    def check_data_availability(self):
        """Wrapper for validate_datasets"""
        result = self.validate_datasets()
        return result["valid"], result


# Standalone wrapper
def check_data_availability():
    manager = HardenedDataIngestionManager()
    return manager.check_data_availability()


# Standalone wrapper for external imports (app.py compatibility)
def check_data_availability():
    """
    Standalone function to check data availability.
    Instantiates manager and checks.
    """
    manager = HardenedDataIngestionManager()
    return manager.check_data_availability()
