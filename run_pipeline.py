#!/usr/bin/env python3

import subprocess
import sys
import time
from pathlib import Path

import yaml


def load_pipeline():
    with open("config/pipeline.yaml", "r") as f:
        return yaml.safe_load(f)["steps"]


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


def main():
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
