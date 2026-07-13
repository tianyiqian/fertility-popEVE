from pathlib import Path

from fertility_popeve.annotation.runner import run_vep
from fertility_popeve.utils.config import load_config


def main():
    config = load_config()

    input_vcf = Path(config["paths"]["joint_test"]) / "joint_chr22.vcf.gz"
    output_vcf = Path(config["paths"]["annotation"]) / "joint_chr22.vep.vcf"

    run_vep(input_vcf, output_vcf)


if __name__ == "__main__":
    main()
