#!/usr/bin/env python3

from pathlib import Path

import pandas as pd

from fertility_popeve.features.popeve import annotate
from fertility_popeve.utils.config import load_config


def main():
    config = load_config()

    protein_file = Path(config["paths"]["protein"]) / "protein_table.parquet"
    output_file = Path(config["paths"]["features"]) / "foundation_features.parquet"

    protein = pd.read_parquet(protein_file)

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

    output_file.parent.mkdir(parents=True, exist_ok=True)

    output.to_parquet(output_file, index=False)

    print(output.head())
    print()
    print(output.columns.tolist())
    print()
    print(f"Total variants: {len(output)}")


if __name__ == "__main__":
    main()
