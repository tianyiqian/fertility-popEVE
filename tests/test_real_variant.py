from pathlib import Path

import pandas as pd
import pytest

from fertility_popeve.variant.record import VariantRecord


def test_real_variant():
    if not Path("data/features/feature_matrix.parquet").exists():
        pytest.skip("Test data not available (data/features/feature_matrix.parquet)")

    df = pd.read_parquet(
        "data/features/feature_matrix.parquet"
    )

    row = df.iloc[0]

    v = VariantRecord(
        sample="TEST",
        chrom=row["chrom"],
        pos=int(row["pos"]),
        ref=row["ref"],
        alt=row["alt"],
        gene=row["gene"],
        popeve=float(row["popEVE"]),
    )

    assert v.chrom.startswith("chr")
    assert v.gene is not None
    assert v.popeve is not None
