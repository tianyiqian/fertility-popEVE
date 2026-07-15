#!/usr/bin/env python3

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fertility_popeve.burden.phenotype_exporter import (
    export_analysis_label_list,
)


def main():
    output = export_analysis_label_list(PROJECT_ROOT / "data" / "geneBurdenRD")
    print(f"[INFO] Wrote {output}")


if __name__ == "__main__":
    main()
