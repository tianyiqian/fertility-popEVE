#!/usr/bin/env python3

import subprocess
import sys

SCRIPTS = [
    "scripts/01_run_vep.py",
    "scripts/02_extract_features.py",
    "scripts/03_filter_missense.py",
    "scripts/04_prepare_protein.py",
    "scripts/05_build_reference_mapping.py",
    "scripts/06_build_popeve_index.py",
    "scripts/07_build_foundation_features.py",
    "scripts/08_build_feature_matrix.py",
    "scripts/09_validate_feature_matrix.py",
]

for script in SCRIPTS:

    print("=" * 60)
    print(script)
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, script]
    )

    if result.returncode != 0:
        print(f"\nERROR: {script} failed.")
        sys.exit(result.returncode)

print("\nPipeline finished successfully.")
