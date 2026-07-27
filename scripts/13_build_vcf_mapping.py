#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fertility_popeve.utils.config import load_config  # noqa: E402

_config = load_config()
VCF_ROOT = Path(os.environ.get("GVCF_ROOT", _config["paths"].get("raw_gvcf", "data/raw_gvcf")))

PHENO = Path(
    "data/phenotype/phenotype.csv"
)

OUT_ALL = Path(
    "data/phenotype/vcf_mapping_all.csv"
)

OUT_PROBAND = Path(
    "data/phenotype/proband_vcf_mapping.csv"
)


def classify_role(path):

    name = str(path).lower()


    # mother
    if any(
        x in name
        for x in [
            "mu",
            "mother",
            "muqin"
        ]
    ):
        return "mother"


    # father
    if any(
        x in name
        for x in [
            "fu",
            "father",
            "fuqin"
        ]
    ):
        return "father"


    # spouse
    if any(
        x in name
        for x in [
            "zhangfu",
            "_0",
            "-0"
        ]
    ):
        return "spouse"


    # proband/self
    if re.search(r'[_-]1', name):
        return "self"


    return "unknown"


def main():

    phenotype = pd.read_csv(PHENO)

    samples = (
        phenotype["sample_id"]
        .astype(str)
        .tolist()
    )

    vcfs = list(
        VCF_ROOT.rglob("*.g.vcf.gz")
    )

    records=[]

    for sid in samples:

        for vcf in vcfs:

            name = vcf.name
            parent = vcf.parent.name

            if sid in name or sid in parent:

                records.append(
                    {
                        "sample_id":sid,
                        "vcf":str(vcf),
                        "role":classify_role(vcf),
                    }
                )


    df=pd.DataFrame(records)

    df.to_csv(
        OUT_ALL,
        index=False
    )


    # select proband

    proband = (
        df[
            df.role=="self"
        ]
        .drop_duplicates(
            "sample_id"
        )
    )


    proband.to_csv(
        OUT_PROBAND,
        index=False
    )


    print("all:")
    print(df.role.value_counts())

    print()

    print("proband:")
    print(
        len(proband)
    )


if __name__=="__main__":
    main()
