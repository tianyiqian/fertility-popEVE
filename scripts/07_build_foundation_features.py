#!/usr/bin/env python3

import pandas as pd

from fertility_popeve.features.popeve import annotate

protein = pd.read_parquet("data/protein/protein_table.parquet")

records = []

for _, row in protein.iterrows():

    result = annotate(
        str(row["chrom"]).replace("chr", ""),
        int(row["pos"]),
        row["ref"],
        row["alt"],
    )

    records.append(result)

feature_df = pd.DataFrame(records)
feature_df = feature_df.rename(columns={
    "protein": "popeve_protein",
    "gene": "popeve_gene",
    "mutant": "popeve_mutant",
})

output = pd.concat(
    [protein.reset_index(drop=True), feature_df],
    axis=1,
)

output.to_parquet(
    "data/features/foundation_features.parquet",
    index=False,
)

print(output.head())
print()
print(output.columns.tolist())
print()
print(f"Total variants: {len(output)}")
