from pathlib import Path

import pandas as pd

from fertility_popeve.gp.builder import (
    build_gp_training_files,
)


def test_build_gp_training_files(tmp_path):

    input_file = tmp_path / "features.parquet"

    df = pd.DataFrame(
        {
            "protein_id": [
                "ENSP1",
                "ENSP1",
            ],
            "position": [
                10,
                20,
            ],
            "ref_aa": [
                "A",
                "G",
            ],
            "alt_aa": [
                "V",
                "D",
            ],
            "EVE": [
                1.5,
                2.5,
            ],
            "found": [
                True,
                False,
            ],
        }
    )

    df.to_parquet(input_file)

    outputs = build_gp_training_files(
        input_file,
        tmp_path / "gp",
    )

    assert len(outputs) == 1

    result = pd.read_csv(outputs[0])

    assert list(result.columns) == [
        "mutant",
        "observed",
        "model_score",
    ]

    assert result.loc[0, "mutant"] == "A10V"
    assert result.loc[1, "observed"] == 0


def test_mapping_file_exists(tmp_path):

    input_file = tmp_path / "features.parquet"

    df = pd.DataFrame(
        {
            "protein_id": ["ENSP1"],
            "position": [10],
            "ref_aa": ["A"],
            "alt_aa": ["V"],
            "EVE": [1.5],
            "found": [True],
        }
    )

    df.to_parquet(input_file)

    build_gp_training_files(
        input_file,
        tmp_path / "gp",
    )

    assert (tmp_path / "gp" / "mapping.csv").exists()


def test_mapping_file_exists(tmp_path):

    input_file = tmp_path / "features.parquet"

    df = pd.DataFrame(
        {
            "protein_id": ["ENSP1"],
            "position": [10],
            "ref_aa": ["A"],
            "alt_aa": ["V"],
            "EVE": [1.5],
            "found": [True],
        }
    )

    df.to_parquet(input_file)

    build_gp_training_files(
        input_file,
        tmp_path / "gp",
    )

    assert (tmp_path / "gp" / "mapping.csv").exists()
