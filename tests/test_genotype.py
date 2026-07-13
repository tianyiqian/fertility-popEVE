from fertility_popeve.variant.genotype import extract_genotype


def test_genotype():

    df = extract_genotype(
        "data/joint_test/joint_chr22.vcf.gz"
    )

    assert len(df) > 0
    assert "sample" in df.columns
    assert "gt" in df.columns
