#!/usr/bin/env python3

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fertility_popeve.gp.candidate_space import build_gp_candidate_space  # noqa: E402
from fertility_popeve.utils.config import load_config  # noqa: E402


def main():
    config = load_config()
    output_file = Path(config["paths"]["gp"]) / "candidate_space.parquet"
    candidates = build_gp_candidate_space(
        config["models"]["popeve_vcf"],
        config["files"]["protein_mapping"],
        Path(config["paths"]["protein"]) / "protein_table.parquet",
        output_file,
        score_columns=["EVE", "ESM1v"],
    )
    print(f"Candidates: {len(candidates)}")
    print(f"Proteins: {candidates['protein_id'].nunique()}")
    print(f"Observed: {int(candidates['cohort_observed'].sum())}")
    print(f"Output: {output_file}")


if __name__ == "__main__":
    main()
