from fertility_popeve.variant.record import VariantRecord


def test_variant_record():

    v = VariantRecord(
        sample="TEST001",
        chrom="1",
        pos=100,
        ref="A",
        alt="G",
        gene="BRCA1",
    )

    assert v.sample == "TEST001"
    assert v.gene == "BRCA1"
