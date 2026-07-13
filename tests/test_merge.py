import pandas as pd

from fertility_popeve.features.merge import merge_features


def test_merge_features():
    a = pd.DataFrame({
        "CHROM": ["1"],
        "POS": [100],
        "REF": ["A"],
        "ALT": ["G"],
        "popeve": [0.92],
    })

    b = pd.DataFrame({
        "CHROM": ["1"],
        "POS": [100],
        "REF": ["A"],
        "ALT": ["G"],
        "burden": [3.4],
    })

    result = merge_features(a, b)

    assert len(result) == 1
    assert result.loc[0, "popeve"] == 0.92
    assert result.loc[0, "burden"] == 3.4
