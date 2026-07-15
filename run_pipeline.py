#!/usr/bin/env python3

import subprocess
import sys
import time

import yaml


def load_pipeline():
    with open("config/pipeline.yaml", "r") as f:
        return yaml.safe_load(f)["steps"]


def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)


def run_step(module):
    print("=" * 60)
    print(f"Running: {module}")
    print("=" * 60)

    start = time.time()

    result = subprocess.run(
        [sys.executable, "-m", module],
    )

    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n❌ Failed: {module}")
        sys.exit(result.returncode)

    print(f"✅ Finished: {module} ({elapsed:.2f}s)\n")


def run_training():

    from fertility_popeve.features.training import (
        build_training_matrix,
        save_training_matrix,
    )

    cfg = load_config()["training"]

    df = build_training_matrix(
        cfg["vcf"],
        cfg["feature"],
        cfg["variant"],
        cfg["phenotype"],
    )

    save_training_matrix(
        df,
        cfg["output"],
    )

    print("=" * 60)
    print("Training matrix generated")
    print(f"Saved: {cfg['output']}")
    print("=" * 60)


def main():

    if len(sys.argv) > 1:

        if sys.argv[1] == "training":
            run_training()
            return

    steps = load_pipeline()

    total_start = time.time()

    for module in steps:
        run_step(module)

    total = time.time() - total_start

    print("=" * 60)
    print("Pipeline completed successfully")
    print(f"Total time: {total:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
