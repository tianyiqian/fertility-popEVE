#!/usr/bin/env python3

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from fertility_popeve.gp.builder import (
    build_gp_training_files,
)

from fertility_popeve.utils.config import (
    load_config,
)


def main():

    config = load_config()

    input_file = (
        Path(config["paths"]["features"])
        /
        "foundation_features.parquet"
    )

    output_dir = (
        Path(config["paths"]["gp"])
        /
        "training"
    )

    outputs = build_gp_training_files(
        input_file,
        output_dir,
        score_column="EVE",
        observed_column="found",
    )

    print(
        f"[INFO] Generated {len(outputs)} protein files"
    )

    print(
        f"[INFO] Output: {output_dir}"
    )


if __name__ == "__main__":
    main()
