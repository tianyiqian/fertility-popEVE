from pathlib import Path

import pandas as pd
import pytest

from fertility_popeve.burden.phenotype_exporter import (
    export_analysis_label_list,
    export_case_control_files,
    validate_phenotype,
)


def create_test_phenotype(path: Path):

    df = pd.DataFrame(
        {
            "sample_id": [
                "S1",
                "S2",
                "S3",
            ],
            "EA": [
                1,
                0,
                None,
            ],
            "NF": [
                0,
                1,
                None,
            ],
            "GV": [
                0,
                0,
                1,
            ],
            "MI": [
                1,
                0,
                0,
            ],
        }
    )

    df.to_csv(
        path,
        index=False,
    )


def test_export_analysis_label_list(tmp_path):

    output = export_analysis_label_list(tmp_path)

    assert output.exists()

    text = output.read_text()

    assert "analysis.label" in text
    assert "EA" in text
    assert "NF" in text
    assert "GV" in text
    assert "MI" in text


def test_export_case_control_files(tmp_path):

    phenotype = tmp_path / "phenotype.csv"

    create_test_phenotype(
        phenotype
    )

    outputs = export_case_control_files(
        phenotype,
        tmp_path,
    )

    assert len(outputs) == 4

    ea = (tmp_path / "EA.tsv").read_text().splitlines()

    assert ea[0] == "sample.id\tcaco"

    assert ea[1] == "S1\t1"


def test_validate_duplicate_sample():

    df = pd.DataFrame(
        {
            "sample_id": [
                "S1",
                "S1",
            ],
            "EA": [1, 0],
            "NF": [0, 1],
            "GV": [0, 0],
            "MI": [0, 0],
        }
    )

    with pytest.raises(ValueError):

        validate_phenotype(df)


def test_validate_invalid_label():

    df = pd.DataFrame(
        {
            "sample_id": [
                "S1",
            ],
            "EA": [
                2,
            ],
            "NF": [
                0,
            ],
            "GV": [
                0,
            ],
            "MI": [
                0,
            ],
        }
    )

    with pytest.raises(ValueError):

        validate_phenotype(df)


def test_validate_missing_column():

    df = pd.DataFrame(
        {
            "sample_id": [
                "S1",
            ],
            "EA": [
                1,
            ],
        }
    )

    with pytest.raises(ValueError):

        validate_phenotype(df)
