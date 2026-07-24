#!/usr/bin/env python3
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from fertility_popeve.gp.trainer import (
    train_eligible_proteins,
    train_eligible_proteins_multi_gpu,
)
from fertility_popeve.utils.config import load_config


def main():
    config = load_config()
    gp_dir = Path(config["paths"]["gp"])
    n_gpu = torch.cuda.device_count()
    mem_cfg = config.get("memory", {})
    subprocess_limit = mem_cfg.get("per_subprocess_limit_gb", 32)

    if n_gpu > 0:
        print(f"[INFO] Detected {n_gpu} GPUs — using multi-GPU parallel training")
        trained = train_eligible_proteins_multi_gpu(
            gp_dir / "training" / "training_readiness.csv",
            gp_dir,
            epochs=config.get("gp_training", {}).get("epochs", 6000),
            holdout_frac=config.get("gp_training", {}).get("holdout_frac", 0.2),
            gpu_ids=list(range(n_gpu)),
            mem_limit_gb=subprocess_limit,
        )
    else:
        print("[INFO] No GPU detected — falling back to CPU serial training")
        from fertility_popeve.utils.memory import set_subprocess_memory_limit
        set_subprocess_memory_limit(subprocess_limit)
        trained = train_eligible_proteins(
            gp_dir / "training" / "training_readiness.csv",
            gp_dir / "models",
            epochs=config.get("gp_training", {}).get("epochs", 6000),
            holdout_frac=config.get("gp_training", {}).get("holdout_frac", 0.2),
            ensemble_mode=True,
            model_names=["EVE", "ESM1V"],
        )

    print(f"[INFO] Trained {len(trained)} proteins")


if __name__ == "__main__":
    main()
