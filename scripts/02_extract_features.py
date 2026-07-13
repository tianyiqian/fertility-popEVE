from pathlib import Path
import pandas as pd

from fertility_popeve.annotation.extractor import (
    get_csq_fields,
    parse_csq,
    extract_feature,
)
from fertility_popeve.utils.config import load_config


def main():
    config = load_config()

    vcf = Path(config["paths"]["annotation"]) / "joint_chr22.vep.vcf"
    out = Path(config["paths"]["annotation"]) / "variant_table.parquet"

    fields = get_csq_fields(vcf)

    rows = []

    with open(vcf) as f:
        for line in f:
            if line.startswith("#"):
                continue

            cols = line.rstrip().split("\t")

            record = {
                "chrom": cols[0],
                "pos": int(cols[1]),
                "ref": cols[3],
                "alt": cols[4],
            }

            csq = parse_csq(cols[7], fields)
            record.update(extract_feature(csq))

            rows.append(record)

    df = pd.DataFrame(rows)
    df.to_parquet(out, index=False)

    print(df.head())
    print(f"\nSaved {len(df)} variants -> {out}")


if __name__ == "__main__":
    main()
