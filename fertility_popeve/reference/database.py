from pathlib import Path

import pandas as pd

_MAPPING = None
_INDEX = None
_TABLE_CACHE = {}


def load_mapping():
    global _MAPPING

    if _MAPPING is None:
        _MAPPING = pd.read_parquet(
            "data/reference/mapping/protein_mapping.parquet"
        )

    return _MAPPING


def load_index():
    global _INDEX

    if _INDEX is None:
        _INDEX = pd.read_parquet(
            "data/reference/popeve_index.parquet"
        )

    return _INDEX


def get_refseq(protein_id: str):

    mapping = load_mapping()

    row = mapping.loc[
        mapping["protein_id"] == protein_id
    ]

    if row.empty:
        return None

    value = row.iloc[0]["refseq_id"]

    if pd.isna(value):
        return None

    return value


def get_feature_path(
    refseq_id: str,
    feature: str,
):

    index = load_index()

    feature = feature.lower()

    row = index.loc[
        (index["refseq_id"] == refseq_id)
        &
        (
            index["feature"]
            .str.lower()
            .str.contains(feature)
        )
    ]

    if row.empty:
        return None

    return row.iloc[0]["path"]


def load_feature_table(
    refseq_id: str,
    feature: str,
):

    key = (refseq_id, feature)

    if key in _TABLE_CACHE:
        return _TABLE_CACHE[key]

    path = get_feature_path(
        refseq_id,
        feature,
    )

    if path is None:
        return None

    df = pd.read_csv(path)

    _TABLE_CACHE[key] = df

    return df
