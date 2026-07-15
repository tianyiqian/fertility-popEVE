from __future__ import annotations

import pandas as pd


def summarize_dataframe(df: pd.DataFrame) -> dict:
    """
    Return a basic summary of a pandas DataFrame.

    Returns
    -------
    dict
        Basic dataframe statistics.
    """
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
    }
