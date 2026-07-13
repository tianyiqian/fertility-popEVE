import pandas as pd

from fertility_popeve.variant.genotype import extract_genotype


def build_training_matrix(
    vcf_path: str,
    feature_path: str,
    phenotype_path: str,
) -> pd.DataFrame:
    """
    Build sample-level training matrix.

    VCF genotype
        +
    popEVE features
        +
    phenotype
    """

    feature = pd.read_parquet(feature_path)

    genotype = extract_genotype(vcf_path)

    phenotype = pd.read_csv(
        phenotype_path
    )

    phenotype = phenotype.rename(
        columns={"sample_id": "sample"}
    )

    merged = genotype.merge(
        feature,
        on=["chrom", "pos", "ref", "alt"],
        how="inner",
    )

    merged = merged.merge(
        phenotype,
        on="sample",
        how="left",
    )

    return merged
