from __future__ import annotations

import pandas as pd


class ExomiserExporter:
    """
    Export fertility-popEVE training matrix to a
    geneBurdenRD-compatible master dataframe.
    """

    def __init__(self, assembly: str = "GRCh38"):
        self.assembly = assembly

    def _build_variant(self, df: pd.DataFrame) -> pd.Series:
        """
        Build Variant column.

        Format:
            chrom:pos:ref:alt
        """
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
        """
        Export minimum geneBurdenRD master dataframe.
        """
        out = pd.DataFrame(index=df.index)

        # Identity block
        out["Sample ID"] = df["sample"]
        out["Gene"] = df["gene"]
        out["Variant"] = self._build_variant(df)

        return out
