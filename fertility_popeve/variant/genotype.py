import subprocess
import pandas as pd


def extract_genotype(vcf_path: str) -> pd.DataFrame:
    """
    Extract sample genotype from VCF.

    Return:
        chrom pos ref alt sample GT
    """

    cmd = [
        "bcftools",
        "query",
        "-f",
        "%CHROM\t%POS\t%REF\t%ALT[\\t%SAMPLE:%GT]\\n",
        vcf_path,
    ]

    output = subprocess.check_output(
        cmd,
        text=True
    )

    rows = []

    for line in output.strip().split("\n"):
        parts = line.split("\t")

        chrom, pos, ref, alt = parts[:4]

        for sample_gt in parts[4:]:
            sample, gt = sample_gt.split(":")
            rows.append(
                {
                    "sample": sample,
                    "chrom": chrom,
                    "pos": int(pos),
                    "ref": ref,
                    "alt": alt,
                    "gt": gt,
                }
            )

    return pd.DataFrame(rows)
