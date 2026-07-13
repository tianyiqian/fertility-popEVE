from fertility_popeve.annotation.extractor import (
    get_csq_fields,
    parse_csq,
    extract_feature,
)

vcf = "data/annotation/joint_chr22.vep.vcf"

fields = get_csq_fields(vcf)

with open(vcf) as f:
    for line in f:
        if line.startswith("#"):
            continue

        info = line.strip().split("\t")[7]
        feature = extract_feature(parse_csq(info, fields))

        for k, v in feature.items():
            print(f"{k}: {v}")

        break
