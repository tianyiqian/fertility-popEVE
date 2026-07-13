#!/usr/bin/env python3

import pandas as pd

INPUT = "data/features/foundation_features.parquet"
OUTPUT = "data/features/feature_matrix.parquet"

df = pd.read_parquet(INPUT)

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

feature_matrix.to_parquet(OUTPUT, index=False)

print(feature_matrix.head())
print()
print(feature_matrix.shape)
print()
print(feature_matrix.dtypes)
