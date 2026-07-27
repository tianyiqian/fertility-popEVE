#!/usr/bin/env python3
"""
Memory watchdog daemon for fertility_popEVE.

Monitors system available memory and kills the heaviest child processes
of a given parent PID when available memory drops below the danger threshold.

Usage:
    # Monitor children of the current process with default config:
    python scripts/00_watchdog.py

    # Monitor children of a specific PID:
    python scripts/00_watchdog.py --pid 12345

    # Custom thresholds:
    python scripts/00_watchdog.py --danger-gb 200 --interval 30
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fertility_popeve.utils.memory import (  # noqa: E402
    available_memory_gb,
    kill_heaviest_processes,
    total_memory_gb,
    used_memory_gb,
)


def main():
    parser = argparse.ArgumentParser(description="Memory watchdog for fertility_popEVE")
    parser.add_argument("--pid", type=int, default=os.getpid(),
                        help="Parent PID whose children to monitor/kill (default: self)")
    parser.add_argument("--danger-gb", type=float, default=200,
                        help="Kill children when available memory drops below this (GB)")
    parser.add_argument("--interval", type=float, default=30,
                        help="Check interval in seconds")
    parser.add_argument("--log", type=str, default="logs/watchdog.log",
                        help="Log file path")
    parser.add_argument("--dry-run", action="store_true",
                        help="Log warnings without actually killing processes")
    args = parser.parse_args()

    Path(args.log).parent.mkdir(parents=True, exist_ok=True)
    log = open(args.log, "a")

    def log_msg(msg):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    log_msg(
        f"Watchdog started. parent_pid={args.pid}, "
        f"danger_threshold={args.danger_gb} GB, "
        f"interval={args.interval}s, "
        f"total_memory={total_memory_gb():.1f} GB"
    )

    kill_count = 0
    while True:
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            log_msg("Watchdog stopped by user.")
            break

        if not Path(f"/proc/{args.pid}").exists():
            log_msg(f"Parent PID {args.pid} no longer exists. Exiting.")
            break

        avail = available_memory_gb()
        used = used_memory_gb()
        total = total_memory_gb()

        if avail >= args.danger_gb:
            continue

        log_msg(
            f"DANGER: {avail:.1f} GB available "
            f"({used:.1f}/{total:.1f} GB used, "
            f"threshold={args.danger_gb} GB)"
        )

        if args.dry_run:
            log_msg("[DRY-RUN] Would kill heaviest child processes.")
            continue

        freed = kill_heaviest_processes(args.pid, max_gb_to_free=100, logger=log_msg)
        kill_count += 1

        if freed > 0:
            log_msg(f"Freed ~{freed:.1f} GB. Now {available_memory_gb():.1f} GB available.")
        else:
            log_msg("No child processes found to kill.")
            if kill_count >= 3:
                log_msg("No killable children found 3 times. Giving up.")
                break

    log.close()


if __name__ == "__main__":
    main()
