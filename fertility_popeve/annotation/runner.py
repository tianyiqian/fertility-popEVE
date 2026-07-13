import subprocess

from fertility_popeve.utils.config import load_config


def run_vep(input_vcf, output_vcf):
    config = load_config()

    cmd = [
        "vep",
        "--cache",
        "--offline",
        "--vcf",
        "--hgvs",
        "--force_overwrite",
        "--fasta", config["paths"]["reference"],
        "-i", str(input_vcf),
        "-o", str(output_vcf),
    ]

    print("Running command:")
    print(" ".join(cmd))

    subprocess.run(cmd, check=True)
