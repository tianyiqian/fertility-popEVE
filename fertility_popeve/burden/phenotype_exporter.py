from pathlib import Path
import pandas as pd


ANALYSES = [
    ("EA", "Embryo Arrest"),
    ("NF", "Fertilization Failure"),
    ("GV", "GV Arrest"),
    ("MI", "MI Arrest"),
]


def export_analysis_label_list(output_dir: str | Path) -> Path:
    """
    Export analysisLabelList.tsv compatible with geneBurdenRD.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(
        ANALYSES,
        columns=["analysis.label", "analysis"],
    )

    output_file = output_dir / "analysisLabelList.tsv"

    df.to_csv(
        output_file,
        sep="\t",
        index=False,
    )

    return output_file
