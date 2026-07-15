from __future__ import annotations

from pathlib import Path

import pandas as pd


MASTER_COLUMNS = [
    "Sample ID",
    "Gene",
    "Variant",
    "Genotypes",
    "ExomiserMOI",
    "Functional Class",
    "Max Freq",
    "GnomAD Freq",
    "De novo",
    "Rank",
    "Score",
    "Variant Score",
    "Pheno Score",
    "Human Pheno Score",
    "Best Evidence",
    "Human Evidence",
    "Mouse Evidence",
    "Fish Evidence",
    "Human PPI Evidence",
    "HGVS",
    "Assembly",
    "Fam Structure",
    "HPO IDs",
    "HPO terms",
    "Exomiser result count",
    "Freq in Exomiser result",
    "CCR Flag",
]


class ExomiserExporter:

    def __init__(self, assembly: str = "GRCh38"):
        self.assembly = assembly

    def _build_variant(self, df: pd.DataFrame) -> pd.Series:
        return (
            df["chrom"].astype(str)
            + ":"
            + df["pos"].astype(str)
            + ":"
            + df["ref"].astype(str)
            + ":"
            + df["alt"].astype(str)
        )

    def export(self, df: pd.DataFrame) -> pd.DataFrame:

        out = pd.DataFrame(index=df.index)

        for c in MASTER_COLUMNS:
            out[c] = pd.NA

        out["Sample ID"] = df["sample"]
        out["Gene"] = df["gene"]
        out["Variant"] = self._build_variant(df)
        out["Genotypes"] = df["gt"]

        out["Functional Class"] = df["consequence"]

        out["Score"] = df["popEVE"]
        out["Variant Score"] = df["popEVE"]

        out["HGVS"] = df["hgvsp"]

        out["Assembly"] = self.assembly

        return out[MASTER_COLUMNS]

    def save(self, df: pd.DataFrame, output: str | Path):

        output = Path(output)

        self.export(df).to_csv(
            output,
            sep="\t",
            index=False,
        )

        return output
