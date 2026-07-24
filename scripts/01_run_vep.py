from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fertility_popeve.annotation.runner import run_vep  # noqa: E402
from fertility_popeve.utils.config import load_config  # noqa: E402


def main():
    config = load_config()

    input_vcf = Path(config["training"]["vcf"])
    vep_output = Path(config["paths"]["annotation"]) / "cohort_joint.vep.vcf.gz"

    run_vep(input_vcf, vep_output)


if __name__ == "__main__":
    main()
