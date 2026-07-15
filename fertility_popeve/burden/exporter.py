from __future__ import annotations

import pandas as pd


class ExomiserExporter:
    """
    Export fertility-popEVE training matrix to a
    geneBurdenRD-compatible master TSV.
    """

    def __init__(self, assembly: str = "GRCh38"):
        self.assembly = assembly

    def export(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert training_matrix into a geneBurdenRD master table.
        """
        raise NotImplementedError
