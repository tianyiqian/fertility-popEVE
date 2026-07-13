from __future__ import annotations

import pandas as pd


def merge_features(*tables: pd.DataFrame) -> pd.DataFrame:
    """
    Merge feature tables by variant.

    Required columns:
        CHROM POS REF ALT
    """

    if not tables:
        raise ValueError("No feature tables provided.")

    merged = tables[0]

    for table in tables[1:]:
        merged = merged.merge(
            table,
            on=["CHROM", "POS", "REF", "ALT"],
            how="left",
        )

    return merged
