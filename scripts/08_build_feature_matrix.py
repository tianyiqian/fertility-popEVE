#!/usr/bin/env python3

from pathlib import Path

import pandas as pd

from fertility_popeve.utils.config import load_config


def main():
    config = load_config()

    input_file = Path(config["paths"]["features"]) / "foundation_features.parquet"
    output_file = Path(config["paths"]["features"]) / "feature_matrix.parquet"

    df = pd.read_parquet(input_file)

    for col in ["popEVE", "EVE", "ESM1v", "gap_frequency"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    feature_matrix = df[
        [
            "chrom",
            "pos",
            "ref",
            "alt",
            "gene",
            "protein_id",
            "position",
            "ref_aa",
            "alt_aa",
            "popEVE",
            "EVE",
            "ESM1v",
            "gap_frequency",
            "found",
        ]
    ].copy()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    feature_matrix.to_parquet(output_file, index=False)

    print(feature_matrix.head())
    print()
    print(feature_matrix.shape)
    print()
    print(feature_matrix.dtypes)


if __name__ == "__main__":
    main()
