import gzip
from pathlib import Path


def get_csq_fields(vcf_file):
    vcf_path = Path(vcf_file)
    opener = gzip.open if vcf_path.suffix == ".gz" else open
    with opener(vcf_path, "rt") as f:
        for line in f:
            if line.startswith("##INFO=<ID=CSQ"):
                prefix = "Format: "
                fields = (
                    line.split(prefix)[1]
                    .split('">')[0]
                    .split("|")
                )
                return fields

    raise ValueError("CSQ header not found.")


def parse_csq(info, csq_fields):
    """
    Parse the first CSQ annotation into a dictionary.
    """

    if "CSQ=" not in info:
        return {}

    csq = info.split("CSQ=")[1].split(";")[0]
    values = csq.split(",")[0].split("|")

    return dict(zip(csq_fields, values))


def extract_feature(record):
    return {
        "gene": record.get("SYMBOL"),
        "gene_id": record.get("Gene"),
        "transcript": record.get("Feature"),
        "consequence": record.get("Consequence"),
        "impact": record.get("IMPACT"),
        "hgvsc": record.get("HGVSc"),
        "hgvsp": record.get("HGVSp"),
        "protein_position": record.get("Protein_position"),
        "amino_acids": record.get("Amino_acids"),
        "hgnc_id": record.get("HGNC_ID"),
    }
