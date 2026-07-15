from __future__ import annotations

from pathlib import Path

import pandas as pd


ANALYSES = [
    ("EA", "Embryo Arrest"),
    ("NF", "Fertilization Failure"),
    ("GV", "GV Arrest"),
    ("MI", "MI Arrest"),
]

REQUIRED_COLUMNS = [
    "sample_id",
    "EA",
    "NF",
    "GV",
    "MI",
]


def load_phenotype(path: str | Path) -> pd.DataFrame:
    """
    Load phenotype table.
    """
    return pd.read_csv(path)


def validate_phenotype(df: pd.DataFrame) -> None:
    """
    Validate phenotype table before export.
    """

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]

    if missing:
        raise ValueError(
            f"Missing required phenotype columns: {', '.join(missing)}"
        )

    if df["sample_id"].duplicated().any():
        dup = df.loc[df["sample_id"].duplicated(), "sample_id"].tolist()
        raise ValueError(f"Duplicated sample_id: {dup}")

    for label, _ in ANALYSES:

        values = df[label].dropna().unique().tolist()

        invalid = [
            v for v in values
            if v not in (0, 1)
        ]

        if invalid:
            raise ValueError(
                f"Invalid values found in column '{label}': {invalid}"
            )


def export_analysis_label_list(
    output_dir: str | Path,
) -> Path:
    """
    Export analysisLabelList.tsv.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    out = pd.DataFrame(
        ANALYSES,
        columns=["analysis.label", "analysis"],
    )

    output = output_dir / "analysisLabelList.tsv"

    out.to_csv(
        output,
        sep="\t",
        index=False,
    )

    return output


def export_case_control_files(
    phenotype_csv: str | Path,
    output_dir: str | Path,
) -> list[Path]:
    """
    Export EA.tsv / NF.tsv / GV.tsv / MI.tsv.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_phenotype(phenotype_csv)

    validate_phenotype(df)

    outputs = []

    for label, _ in ANALYSES:

        out = pd.DataFrame()

        out["sample.id"] = df["sample_id"]

        out["caco"] = (
            df[label]
            .astype("Int64")
            .astype("string")
            .fillna("NA")
        )

        outfile = output_dir / f"{label}.tsv"

        out.to_csv(
            outfile,
            sep="\t",
            index=False,
        )

        outputs.append(outfile)

    return outputs


def export_all(
    phenotype_csv: str | Path,
    output_dir: str | Path,
) -> list[Path]:
    """
    Export all GeneBurdenRD phenotype files.
    """

    outputs = []

    outputs.append(
        export_analysis_label_list(output_dir)
    )

    outputs.extend(
        export_case_control_files(
            phenotype_csv,
            output_dir,
        )
    )

    return outputs

