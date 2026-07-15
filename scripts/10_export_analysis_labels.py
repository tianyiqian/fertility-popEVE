#!/usr/bin/env python3

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fertility_popeve.burden.phenotype_exporter import (
    export_all,
)


def main():

    phenotype_file = (
        PROJECT_ROOT
        / "data"
        / "phenotype"
        / "phenotype.csv"
    )

    output_dir = (
        PROJECT_ROOT
        / "data"
        / "geneBurdenRD"
    )

    outputs = export_all(
        phenotype_file,
        output_dir,
    )

    for output in outputs:
        print(f"[INFO] Wrote {output}")


if __name__ == "__main__":
    main()
