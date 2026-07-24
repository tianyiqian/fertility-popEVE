#!/usr/bin/env python3
"""Create an auditable, exact-match gVCF manifest for the fertility cohort."""

from pathlib import Path
import pandas as pd


PHENOTYPE = Path("data/phenotype/phenotype.csv")
EXISTING_PROBAND_MAP = Path("data/phenotype/proband_vcf_mapping.csv")
OUT_DIR = Path("data/cohort")


def sample_token(vcf: Path) -> str:
    """DeepVariant files begin with `<sample_id>_1_...`; never use substring matching."""
    return vcf.name.split("_", 1)[0]


def main():
    phenotype = pd.read_csv(PHENOTYPE)
    expected = set(phenotype["sample_id"].dropna().astype(str))
    existing = pd.read_csv(EXISTING_PROBAND_MAP)
    existing["sample_id"] = existing["sample_id"].astype(str)
    existing = existing[existing["sample_id"].isin(expected)].copy()
    existing["token"] = existing["vcf"].map(lambda value: sample_token(Path(value)))
    # The old map used substring matching. Keep only rows whose file token is exact.
    mapping = existing[existing["sample_id"] == existing["token"]][["sample_id", "vcf"]]
    mapping = mapping.drop_duplicates().sort_values(["sample_id", "vcf"])
    duplicated = mapping[mapping.duplicated("sample_id", keep=False)]
    if not duplicated.empty:
        raise ValueError(
            "A sample ID maps to multiple gVCFs; resolve before joint calling: "
            f"{duplicated.sample_id.unique().tolist()[:10]}"
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mapping.to_csv(OUT_DIR / "proband_gvcf_mapping_exact.csv", index=False)
    mapping["vcf"].to_csv(OUT_DIR / "proband_gvcfs.list", index=False, header=False)

    matched = set(mapping["sample_id"])
    pd.DataFrame({"sample_id": sorted(expected - matched)}).to_csv(
        OUT_DIR / "unmatched_phenotype_samples.csv", index=False
    )
    print(f"Matched unique probands: {len(mapping)}")
    print(f"Unmatched phenotype samples: {len(expected - matched)}")
    print(f"Manifest: {OUT_DIR / 'proband_gvcfs.list'}")


if __name__ == "__main__":
    main()
