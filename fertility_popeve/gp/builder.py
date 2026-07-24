from pathlib import Path

import numpy as np
import pandas as pd


def build_mutant(ref_aa, position, alt_aa):
    return f"{ref_aa}{int(position)}{alt_aa}"


def _prepare_training_data(df, score_columns, observed_column):
    """Validate and standardize the per-variant input table for GP training."""
    required = {"protein_id", "position", "ref_aa", "alt_aa"} | set(score_columns) | {observed_column}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    prepared = df.copy()
    prepared["mutant"] = prepared.apply(
        lambda row: build_mutant(row["ref_aa"], row["position"], row["alt_aa"]),
        axis=1,
    )
    prepared["observed"] = pd.to_numeric(prepared[observed_column], errors="coerce")

    invalid_observed = prepared["observed"].isna() | ~prepared["observed"].isin([0, 1])
    if invalid_observed.any():
        raise ValueError(
            f"{observed_column} must contain only binary 0/1 values; "
            f"found {invalid_observed.sum()} invalid rows."
        )

    for col in score_columns:
        invalid_scores = ~np.isfinite(prepared[col])
        if invalid_scores.any():
            raise ValueError(
                f"{col} must contain finite numeric values; "
                f"found {invalid_scores.sum()} invalid rows."
            )

    duplicate_keys = prepared.duplicated(["protein_id", "mutant"], keep=False)
    if duplicate_keys.any():
        examples = prepared.loc[duplicate_keys, ["protein_id", "mutant"]].head(5)
        raise ValueError(
            "Duplicate protein/mutant rows cannot be used for GP training. "
            f"Examples: {examples.to_dict(orient='records')}"
        )

    return prepared


def build_gp_training_files(
    input_file,
    output_dir,
    score_columns=None,
    observed_column="cohort_observed",
    min_variants_for_training=100,
    min_observed_for_training=10,
):
    """Build per-protein, per-evo-model GP input files and a readiness report.

    For each evo model (score column) and each protein, a CSV with columns
    ``mutant, observed, model_score`` is written.  The companion
    ``training_readiness.csv`` records whether each protein × model unit
    has enough data for training.
    """
    if score_columns is None:
        score_columns = ["eve_score"]
    if min_variants_for_training < 1 or min_observed_for_training < 1:
        raise ValueError("Training thresholds must be at least 1.")

    input_file = Path(input_file)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = _prepare_training_data(
        pd.read_parquet(input_file),
        score_columns=score_columns,
        observed_column=observed_column,
    )

    outputs = []
    mapping = []

    for protein, group in df.groupby("protein_id", sort=True):
        for col in score_columns:
            model_name = col.replace("_score", "").upper()
            out = group[["mutant", "observed", col]].copy()
            out = out.rename(columns={col: "model_score"}).sort_values("mutant")
            out["model_score"] = pd.to_numeric(out["model_score"], errors="coerce")
            out = out.dropna(subset=["model_score"])
            filename = f"{protein}_{model_name}.csv"
            output_file = output_dir / filename
            out.to_csv(output_file, index=False)
            outputs.append(output_file)

            seen_count = int(out["observed"].sum())
            not_seen_count = int((out["observed"] == 0).sum())
            mapping.append(
                {
                    "evo_model": model_name,
                    "protein_id": protein,
                    "counter": len(out),
                    "unique_id": f"{protein}_{model_name}_{len(out)}",
                    "seen_count": seen_count,
                    "not_seen_count": not_seen_count,
                    "eligible_for_training": (
                        len(out) >= min_variants_for_training
                        and seen_count >= min_observed_for_training
                        and not_seen_count > 0
                    ),
                    "file_path": str(output_file),
                }
            )

    mapping_df = pd.DataFrame(mapping)
    mapping_df.to_csv(output_dir / "mapping.csv", index=False)
    mapping_df.to_csv(output_dir / "training_readiness.csv", index=False)

    return outputs
