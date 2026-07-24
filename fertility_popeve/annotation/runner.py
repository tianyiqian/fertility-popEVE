import subprocess

from fertility_popeve.utils.config import load_config


def run_vep(input_vcf, output_vcf):
    config = load_config()
    vep_config = config.get("vep", {})

    cmd = [
        "vep",
        "--cache",
        "--offline",
        "--vcf",
        "--hgvs",
        "--force_overwrite",
        "--fasta", config["paths"]["reference"],
        "--fork", str(vep_config.get("fork", 4)),
        "--compress_output", "bgzip",
        "--buffer_size", str(vep_config.get("buffer_size", 500000)),
        "-i", str(input_vcf),
        "-o", str(output_vcf),
    ]

    if "custom" in vep_config:
        for custom_entry in vep_config["custom"]:
            cmd.extend(["--custom", custom_entry])

    print("Running VEP command:")
    print(" ".join(str(c) for c in cmd))

    subprocess.run(cmd, check=True)
