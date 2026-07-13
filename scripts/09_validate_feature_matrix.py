#!/usr/bin/env python3

from pathlib import Path

import pandas as pd

from fertility_popeve.utils.config import load_config


def main():
    config = load_config()

    file = Path(config["paths"]["features"]) / "feature_matrix.parquet"

    df = pd.read_parquet(file)

    print("=" * 60)
    print("Feature Matrix Validation")
    print("=" * 60)

    print(f"Rows    : {len(df)}")
    print(f"Columns : {len(df.columns)}")
    print()

    print("Duplicate variants:")
    dup = df.duplicated(subset=["chrom", "pos", "ref", "alt"]).sum()
    print(dup)
    print()

    print("Coverage:")
    print(df["found"].value_counts())
    print()

    print("Missing values:")
    print(df.isna().sum())
    print()

    print("Data types:")
    print(df.dtypes)
    print()

    print("Numeric summary:")
    print(df[["popEVE", "EVE", "ESM1v"]].describe())


if __name__ == "__main__":
    main()
