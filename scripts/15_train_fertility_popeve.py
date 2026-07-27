#!/usr/bin/env python3
"""Train per-protein popEVE GP models.

Aligned with the training methodology from:

    Orenbuch et al. "Deep generative modeling of the human proteome
    reveals over a hundred novel genes involved in rare genetic
    disorders."  medRxiv, 2023.

Output directories mirror the official ``train_popEVE_models.sh`` layout:
    {gp_dir}/states/                  — model checkpoint .pth files
    {gp_dir}/scores/                  — per-variant score CSVs
    {gp_dir}/losses_and_lengthscales/ — training history CSVs
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import torch  # noqa: E402

from fertility_popeve.gp.trainer import (  # noqa: E402
    train_eligible_proteins,
    train_eligible_proteins_multi_gpu,
)
from fertility_popeve.utils.config import load_config  # noqa: E402


def main():
    config = load_config()
    gp_cfg = config.get("gp_training", {})

    gp_dir = Path(config["paths"]["gp"])
    epochs = gp_cfg.get("epochs", 6000)
    training_frac = gp_cfg.get("training_frac", 1.0)
    checkpoint_every = gp_cfg.get("checkpoint_every", 1000)
    convergence_patience = gp_cfg.get("convergence_patience", 0)

    n_gpu = torch.cuda.device_count()
    mem_cfg = config.get("memory", {})
    subprocess_limit = mem_cfg.get("per_subprocess_limit_gb", 32)

    if n_gpu > 0:
        print(f"[INFO] Detected {n_gpu} GPUs — using multi-GPU parallel training")
        trained = train_eligible_proteins_multi_gpu(
            gp_dir / "training" / "training_readiness.csv",
            gp_dir,
            epochs=epochs,
            training_frac=training_frac,
            gpu_ids=list(range(n_gpu)),
            mem_limit_gb=subprocess_limit,
            checkpoint_every=checkpoint_every,
            convergence_patience=convergence_patience,
        )
    else:
        print("[INFO] No GPU detected — falling back to CPU serial training")
        from fertility_popeve.utils.memory import set_subprocess_memory_limit
        set_subprocess_memory_limit(subprocess_limit)
        trained = train_eligible_proteins(
            gp_dir / "training" / "training_readiness.csv",
            gp_dir,
            epochs=epochs,
            training_frac=training_frac,
            ensemble_mode=True,
            model_names=["EVE", "ESM1V"],
            checkpoint_every=checkpoint_every,
            convergence_patience=convergence_patience,
        )

    print(f"[INFO] Trained {len(trained)} proteins")
    print(f"[INFO] Checkpoints: {gp_dir / 'states'}")
    print(f"[INFO] Scores:      {gp_dir / 'scores'}")
    print(f"[INFO] Losses:      {gp_dir / 'losses_and_lengthscales'}")


if __name__ == "__main__":
    main()
