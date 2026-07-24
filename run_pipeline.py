#!/usr/bin/env python3

import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from fertility_popeve.utils.memory import (
    available_memory_gb,
    wait_for_memory,
    launch_watchdog,
)


def load_pipeline():
    with open("config/pipeline.yaml", "r") as f:
        return yaml.safe_load(f)["steps"]


def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)


def run_step(module, mem_cfg=None):
    print("=" * 60)
    print(f"Running: {module}")
    print("=" * 60)

    if mem_cfg:
        safe = mem_cfg.get("safe_threshold_gb", 500)
        avail = available_memory_gb()
        if avail < safe:
            print(f"  [MEMORY] Only {avail:.1f} GB available, waiting for {safe:.0f} GB...")
            wait_for_memory(safe, label=module)

    start = time.time()

    result = subprocess.run([sys.executable, "-m", module])

    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\nFailed: {module}")
        sys.exit(result.returncode)

    print(f"Finished: {module} ({elapsed:.2f}s)\n")


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

    config = load_config()
    mem_cfg = config.get("memory", {})
    steps = load_pipeline()

    wd_proc = None
    danger_gb = mem_cfg.get("danger_threshold_gb", 200)
    interval = mem_cfg.get("watchdog_interval_sec", 30)
    if danger_gb > 0:
        print(f"[INFO] Launching memory watchdog (threshold={danger_gb} GB, interval={interval}s)")
        wd_proc = launch_watchdog(
            parent_pid=os.getpid(),
            danger_threshold_gb=danger_gb,
            interval_sec=interval,
        )

    total_start = time.time()
    failed = False

    try:
        for module in steps:
            run_step(module, mem_cfg)
    except Exception:
        failed = True
        raise
    finally:
        if wd_proc is not None:
            print("[INFO] Stopping watchdog...")
            wd_proc.terminate()
            wd_proc.wait(timeout=5)

    if not failed:
        total = time.time() - total_start
        print("=" * 60)
        print("Pipeline completed successfully")
        print(f"Total time: {total:.2f}s")
        print("=" * 60)


if __name__ == "__main__":
    main()
