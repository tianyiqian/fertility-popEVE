#!/usr/bin/env python3

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fertility_popeve.gp.builder import build_gp_training_files  # noqa: E402
from fertility_popeve.utils.config import load_config  # noqa: E402


def main():
    config = load_config()
    input_file = Path(config["paths"]["gp"]) / "candidate_space.parquet"
    output_dir = Path(config["paths"]["gp"]) / "training"

    outputs = build_gp_training_files(
        input_file,
        output_dir,
        score_columns=["eve_score", "esm1v_score"],
        observed_column="cohort_observed",
        min_variants_for_training=20,
        min_observed_for_training=3,
    )

    print(f"[INFO] Generated {len(outputs)} protein files")
    print(f"[INFO] Output: {output_dir}")


if __name__ == "__main__":
    main()
