import pandas as pd

from fertility_popeve.variant.genotype import extract_genotype


def build_training_matrix(
    vcf_path: str,
    feature_path: str,
    variant_path: str,
    phenotype_path: str,
) -> pd.DataFrame:

    feature = pd.read_parquet(feature_path)

    variant = pd.read_parquet(variant_path)

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
        variant[
            [
                "chrom",
                "pos",
                "ref",
                "alt",
                "consequence",
                "impact",
                "hgvsc",
                "hgvsp",
            ]
        ],
        on=["chrom", "pos", "ref", "alt"],
        how="left",
    )

    merged = merged.merge(
        phenotype,
        on="sample",
        how="left",
    )

    return merged


def save_training_matrix(
    df: pd.DataFrame,
    output_path: str,
):
    df.to_parquet(
        output_path,
        index=False,
    )
