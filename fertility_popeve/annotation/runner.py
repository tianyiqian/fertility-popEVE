import subprocess


def run_vep(input_vcf, output_vcf):
    cmd = [
        "vep",
        "--cache",
        "--offline",
        "--vcf",
        "--force_overwrite",
        "-i", str(input_vcf),
        "-o", str(output_vcf),
    ]

    print("Running command:")
    print(" ".join(cmd))

    subprocess.run(cmd, check=True)
