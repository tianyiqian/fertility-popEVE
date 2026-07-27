from pathlib import Path

import pytest

from fertility_popeve.variant.genotype import extract_genotype


def test_genotype():
    if not Path("data/joint_test/joint_chr22.vcf.gz").exists():
        pytest.skip("Test data not available (data/joint_test/joint_chr22.vcf.gz)")

    df = extract_genotype(
        "data/joint_test/joint_chr22.vcf.gz"
    )

    assert len(df) > 0
    assert "sample" in df.columns
    assert "gt" in df.columns
