import pandas as pd

from fertility_popeve.features.training import build_training_matrix


def test_training_matrix():

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
        phenotype,
    )

    assert len(df) > 0
    assert "popEVE" in df.columns
    assert "phenotype" in df.columns
