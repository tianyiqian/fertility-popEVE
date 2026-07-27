#!/usr/bin/env python3

import re
from pathlib import Path

import pandas as pd

from fertility_popeve.utils.config import load_config


def main():

    cfg = load_config()

    data_dir = Path(cfg["models"]["popeve"])

    records = []

    pattern = re.compile(
        r"^(NP_[^_]+\.\d+)_(.+)\.csv$"
    )

    for csv_file in sorted(data_dir.glob("*.csv")):

        m = pattern.match(csv_file.name)

        if m is None:
            continue

        refseq = m.group(1)

        feature = m.group(2)

        records.append(
            {
                "refseq_id": refseq,
                "feature": feature,
                "filename": csv_file.name,
                "path": str(csv_file),
            }
        )

    df = pd.DataFrame(records)

    out = (
        Path(cfg["paths"]["reference_data"])
        / "popeve_index.parquet"
    )

    out.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_parquet(out, index=False)

    print(df)
    print()
    print(f"Total CSV: {len(df)}")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
