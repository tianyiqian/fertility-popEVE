from __future__ import annotations

from pathlib import Path

import pandas as pd


class ExomiserExporter:
    """
    Export fertility-popEVE training matrix to a
    geneBurdenRD-compatible master dataframe.
    """

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

        out["Sample ID"] = df["sample"]
        out["Gene"] = df["gene"]
        out["Variant"] = self._build_variant(df)
        out["Genotypes"] = df["gt"]
        out["Assembly"] = self.assembly

        return out

    def save(self, df: pd.DataFrame, output: str | Path) -> Path:
        """
        Export dataframe and save as TSV.
        """
        output = Path(output)

        out = self.export(df)

        out.to_csv(
            output,
            sep="\t",
            index=False,
        )

        return output
