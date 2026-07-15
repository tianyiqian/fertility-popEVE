from pathlib import Path

import pandas as pd


def build_mutant(ref_aa, position, alt_aa):
    """
    Convert amino acid change into popEVE format.

    Example:
        P771T
    """

    return f"{ref_aa}{int(position)}{alt_aa}"


def build_gp_training_files(
    input_file,
    output_dir,
    score_column="EVE",
    observed_column="found",
):
    """
    Build protein-specific GP training files.

    Output:

    protein.csv
    mapping.csv

    CSV format:

    mutant,observed,model_score
    """

    input_file = Path(input_file)
    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.read_parquet(input_file)

    required = [
        "protein_id",
        "position",
        "ref_aa",
        "alt_aa",
        score_column,
        "found",
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    df = df.copy()

    df["mutant"] = df.apply(
        lambda x: build_mutant(
            x["ref_aa"],
            x["position"],
            x["alt_aa"],
        ),
        axis=1,
    )

    df["observed"] = (
        df[observed_column]
        .astype(int)
    )

    df["model_score"] = (
        df[score_column]
        .astype(float)
    )

    outputs = []
    mapping = []

    for protein, group in df.groupby(
        "protein_id"
    ):

        out = group[
            [
                "mutant",
                "observed",
                "model_score",
            ]
        ]

        output_file = (
            output_dir /
            f"{protein}.csv"
        )

        out.to_csv(
            output_file,
            index=False,
        )

        outputs.append(output_file)

        mapping.append(
            {
                "protein_id": protein,
                "file_path": str(output_file),
            }
        )

    mapping_file = output_dir / "mapping.csv"

    pd.DataFrame(mapping).to_csv(
        mapping_file,
        index=False,
    )

    return outputs
