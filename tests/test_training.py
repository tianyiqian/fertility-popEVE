from pathlib import Path

import pandas as pd
import pytest

from fertility_popeve.features.training import build_training_matrix


def test_training_matrix():
    required = [
        "data/joint_test/joint_chr22.vcf.gz",
        "data/features/feature_matrix.parquet",
        "data/annotation/variant_table.parquet",
    ]
    if not all(Path(f).exists() for f in required):
        pytest.skip("Test data not available: " + ", ".join(required))

    phenotype = "tests/test_phenotype.csv"

    pd.DataFrame(
        {
            "sample_id": [
                "18R21164"
            ],
            "phenotype": [
                1
            ],
        }
    ).to_csv(
        phenotype,
        index=False,
    )

    df = build_training_matrix(
        "data/joint_test/joint_chr22.vcf.gz",
        "data/features/feature_matrix.parquet",
        "data/annotation/variant_table.parquet",
        phenotype,
    )

    assert len(df) > 0

    assert "popEVE" in df.columns
    assert "phenotype" in df.columns

    assert "consequence" in df.columns
    assert "impact" in df.columns
    assert "hgvsc" in df.columns
    assert "hgvsp" in df.columns


def test_save_training_matrix(tmp_path):

    from fertility_popeve.features.training import save_training_matrix

    df = pd.DataFrame(
        {
            "sample": ["TEST001"],
            "popEVE": [0.5],
        }
    )

    out = tmp_path / "training.parquet"

    save_training_matrix(
        df,
        out,
    )

    assert out.exists()

    loaded = pd.read_parquet(out)

    assert loaded.shape == (1, 2)
