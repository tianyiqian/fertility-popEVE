import pandas as pd

from fertility_popeve.gp.builder import build_gp_training_files


def _write_features(path, observed_column="cohort_observed", observed=(1, 0)):
    pd.DataFrame(
        {
            "protein_id": ["ENSP1"] * len(observed),
            "position": list(range(10, 10 * (len(observed) + 1), 10)),
            "ref_aa": ["A", "G", "S"][: len(observed)],
            "alt_aa": ["V", "D", "T"][: len(observed)],
            "eve_score": [1.5, 2.5, 3.5][: len(observed)],
            observed_column: observed,
        }
    ).to_parquet(path)


def test_build_gp_training_files(tmp_path):
    input_file = tmp_path / "features.parquet"
    _write_features(input_file)

    outputs = build_gp_training_files(input_file, tmp_path / "gp")

    assert len(outputs) == 1
    result = pd.read_csv(outputs[0])
    assert list(result.columns) == ["mutant", "observed", "model_score"]
    assert result.loc[0, "mutant"] == "A10V"
    assert result.loc[1, "observed"] == 0
    assert outputs[0].name == "ENSP1_EVE.csv"


def test_uses_configured_observed_column_and_writes_readiness(tmp_path):
    input_file = tmp_path / "features.parquet"
    _write_features(input_file, observed_column="cohort_observed", observed=(1, 0, 0))

    output_dir = tmp_path / "gp"
    build_gp_training_files(
        input_file,
        output_dir,
        observed_column="cohort_observed",
        min_variants_for_training=3,
        min_observed_for_training=1,
    )

    readiness = pd.read_csv(output_dir / "training_readiness.csv")
    assert readiness.loc[0, "seen_count"] == 1
    assert readiness.loc[0, "not_seen_count"] == 2
    assert readiness.loc[0, "eligible_for_training"]
    assert readiness.loc[0, "unique_id"] == "ENSP1_EVE_3"


def test_rejects_invalid_scores(tmp_path):
    input_file = tmp_path / "features.parquet"
    _write_features(input_file)
    frame = pd.read_parquet(input_file)
    frame.loc[0, "eve_score"] = float("nan")
    frame.to_parquet(input_file)

    try:
        build_gp_training_files(input_file, tmp_path / "gp")
    except ValueError as error:
        assert "finite numeric values" in str(error)
    else:
        raise AssertionError("Expected invalid GP input to be rejected.")


def test_multi_model_build(tmp_path):
    input_file = tmp_path / "features.parquet"
    pd.DataFrame(
        {
            "protein_id": ["ENSP1", "ENSP1"],
            "position": [10, 20],
            "ref_aa": ["A", "G"],
            "alt_aa": ["V", "D"],
            "eve_score": [1.5, 2.5],
            "esm1v_score": [0.5, -1.2],
            "cohort_observed": [1, 0],
        }
    ).to_parquet(input_file)

    output_dir = tmp_path / "gp_multi"
    outputs = build_gp_training_files(
        input_file,
        output_dir,
        score_columns=["eve_score", "esm1v_score"],
        min_variants_for_training=2,
        min_observed_for_training=1,
    )

    assert len(outputs) == 2
    assert outputs[0].name == "ENSP1_EVE.csv"
    assert outputs[1].name == "ENSP1_ESM1V.csv"
    readiness = pd.read_csv(output_dir / "training_readiness.csv")
    assert len(readiness) == 2
    assert readiness["evo_model"].tolist() == ["EVE", "ESM1V"]
