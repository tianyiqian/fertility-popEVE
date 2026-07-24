import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from fertility_popeve.gp.trainer import (
    _normalise_scores,
    _percentiles_from_samples,
    train_protein_gp,
)


class TestNormaliseScores:
    def test_basic_normalisation(self):
        scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)
        norm, lo, hi = _normalise_scores(scores)
        assert lo == 1.0
        assert hi == 5.0
        assert norm[0] == 0.0
        assert norm[-1] == 1.0

    def test_constant_scores_raise(self):
        with pytest.raises(ValueError, match="Constant"):
            _normalise_scores(np.array([3.0, 3.0, 3.0], dtype=np.float32))

    def test_negative_scores(self):
        scores = np.array([-10.0, -5.0, 0.0], dtype=np.float32)
        norm, lo, hi = _normalise_scores(scores)
        assert lo == -10.0
        assert hi == 0.0


class TestPercentilesFromSamples:
    def test_output_length(self):
        samples = torch.rand(1000, 5)
        results = _percentiles_from_samples(samples)
        assert len(results) == 3

    def test_order(self):
        samples = torch.rand(1000, 10)
        lower, median, upper = _percentiles_from_samples(samples)
        for i in range(samples.size(1)):
            assert lower[i] <= median[i] <= upper[i]


class TestTrainProteinGP:
    @pytest.fixture
    def synthetic_training_csv(self):
        np.random.seed(42)
        n = 200
        model_score = np.random.uniform(0, 1, n)
        observed = (model_score > 0.7).astype(int)
        df = pd.DataFrame({"model_score": model_score, "observed": observed})
        with tempfile.NamedTemporaryFile(
            suffix=".csv", mode="w", delete=False
        ) as f:
            df.to_csv(f.name, index=False)
            yield f.name
        Path(f.name).unlink(missing_ok=True)

    def test_training_produces_outputs(self, synthetic_training_csv):
        with tempfile.TemporaryDirectory() as tmpdir:
            history = train_protein_gp(
                synthetic_training_csv,
                tmpdir,
                epochs=50,
                training_frac=1.0,
                checkpoint_every=0,
                convergence_patience=0,
            )
            assert len(history) == 50
            assert (Path(tmpdir) / "states").exists()
            assert (Path(tmpdir) / "scores").exists()
            assert (Path(tmpdir) / "losses_and_lengthscales").exists()

    def test_training_with_holdout(self, synthetic_training_csv):
        with tempfile.TemporaryDirectory() as tmpdir:
            history = train_protein_gp(
                synthetic_training_csv,
                tmpdir,
                epochs=30,
                training_frac=0.8,
                checkpoint_every=0,
                convergence_patience=0,
            )
            assert len(history) == 30

    def test_checkpoint_saving(self, synthetic_training_csv):
        with tempfile.TemporaryDirectory() as tmpdir:
            train_protein_gp(
                synthetic_training_csv,
                tmpdir,
                epochs=20,
                training_frac=1.0,
                checkpoint_every=10,
                convergence_patience=0,
            )
            states = list((Path(tmpdir) / "states").glob("*_model_*.pth"))
            assert len(states) >= 1

    def test_scores_columns(self, synthetic_training_csv):
        with tempfile.TemporaryDirectory() as tmpdir:
            train_protein_gp(
                synthetic_training_csv,
                tmpdir,
                epochs=20,
                training_frac=1.0,
                checkpoint_every=0,
                convergence_patience=0,
            )
            scores = pd.read_csv(next((Path(tmpdir) / "scores").glob("*_scores.csv")))
            for col in ("X", "GP_mean", "GP_lower", "GP_upper",
                         "GP_mean_all_samples", "mean_prob"):
                assert col in scores.columns, f"Missing column: {col}"

    def test_single_class_raises(self):
        with tempfile.NamedTemporaryFile(
            suffix=".csv", mode="w", delete=False
        ) as f:
            pd.DataFrame({
                "model_score": [0.5, 0.6, 0.7],
                "observed": [0, 0, 0],
            }).to_csv(f.name, index=False)
            path = f.name
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                with pytest.raises(ValueError, match="both observed classes"):
                    train_protein_gp(
                        path, tmpdir, epochs=5, checkpoint_every=0,
                    )
        finally:
            Path(path).unlink(missing_ok=True)
