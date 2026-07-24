from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def _parse_meminfo() -> dict[str, int]:
    info = {}
    with open("/proc/meminfo", "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                key = parts[0].rstrip(":")
                value = int(parts[1])  # kB
                info[key] = value
    return info


def available_memory_gb() -> float:
    info = _parse_meminfo()
    available_kb = info.get("MemAvailable", 0)
    return available_kb / (1024 * 1024)


def total_memory_gb() -> float:
    info = _parse_meminfo()
    total_kb = info.get("MemTotal", 0)
    return total_kb / (1024 * 1024)


def used_memory_gb() -> float:
    return total_memory_gb() - available_memory_gb()


def ensure_enough_memory(required_gb: float, label: str = "stage"):
    available = available_memory_gb()
    if available < required_gb:
        raise MemoryError(
            f"Not enough memory before {label}: "
            f"{available:.1f} GB available, need at least {required_gb:.0f} GB"
        )


def wait_for_memory(required_gb: float, label: str = "stage", poll_sec: int = 30):
    while True:
        available = available_memory_gb()
        if available >= required_gb:
            return
        print(
            f"  [MEMORY] {label}: {available:.1f} GB available, "
            f"need {required_gb:.0f} GB, waiting {poll_sec}s..."
        )
        time.sleep(poll_sec)


def set_subprocess_memory_limit(max_gb: float):
    import resource

    limit_bytes = int(max_gb * 1024 * 1024 * 1024)
    try:
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
    except ValueError:
        pass


def _rss_by_pid(pid: int) -> int:
    try:
        with open(f"/proc/{pid}/statm", "r") as f:
            fields = f.readline().strip().split()
            rss_pages = int(fields[1])
            page_size = os.sysconf(os.sysconf_names["SC_PAGE_SIZE"])
            return rss_pages * page_size
    except (FileNotFoundError, ProcessLookupError):
        return 0


def _children_pids(parent: int) -> list[int]:
    pids = []
    for entry in Path("/proc").iterdir():
        if not entry.is_dir():
            continue
        pid_str = entry.name
        if not pid_str.isdigit():
            continue
        try:
            stat = (entry / "stat").read_text()
        except (FileNotFoundError, PermissionError):
            continue
        parts = stat.split(")", 1)
        if len(parts) < 2:
            continue
        rest = parts[1].strip().split()
        if len(rest) < 2:
            continue
        ppid = int(rest[1])
        if ppid == parent:
            pids.append(int(pid_str))
    return pids


def _all_descendants(pid: int) -> list[int]:
    result = []
    stack = [pid]
    while stack:
        p = stack.pop()
        children = _children_pids(p)
        result.extend(children)
        stack.extend(children)
    return result


def get_heaviest_children(parent_pid: int) -> list[tuple[int, float]]:
    all_pids = _all_descendants(parent_pid)
    if not all_pids:
        return []
    with_size = [(p, _rss_by_pid(p) / (1024**3)) for p in all_pids]
    with_size.sort(key=lambda x: x[1], reverse=True)
    return with_size


def kill_heaviest_processes(parent_pid: int, max_gb_to_free: float, logger=None):
    children = get_heaviest_children(parent_pid)
    if not children:
        return 0.0
    freed = 0.0
    killed = []
    for pid, gb in children:
        if freed >= max_gb_to_free:
            break
        try:
            proc_name = Path(f"/proc/{pid}/cmdline").read_text().replace("\x00", " ").strip()[:120]
        except (FileNotFoundError, PermissionError):
            proc_name = f"PID {pid}"
        msg = f"Killing PID {pid} ({proc_name}) — {gb:.1f} GB RSS"
        if logger:
            logger(msg)
        else:
            print(msg)
        try:
            os.kill(pid, signal.SIGTERM)
            killed.append((pid, gb))
            freed += gb
        except (ProcessLookupError, PermissionError):
            pass
    if killed:
        time.sleep(5)
    return freed


def launch_watchdog(
    parent_pid: int,
    danger_threshold_gb: float,
    interval_sec: float = 30,
    log_file: str = "logs/watchdog.log",
):
    project_root = Path(__file__).resolve().parents[2]
    script = (
        f"import os, sys, signal, time\n"
        f"sys.path.insert(0, {project_root!r})\n"
        f"from fertility_popeve.utils.memory import available_memory_gb, kill_heaviest_processes\n\n"
        f"log = open({log_file!r}, 'a')\n"
        f"def log_msg(msg):\n"
        f"    ts = time.strftime('%Y-%m-%d %H:%M:%S')\n"
        f"    line = f'[{{ts}}] {{msg}}'\n"
        f"    print(line, flush=True)\n"
        f"    log.write(line + '\\n')\n"
        f"    log.flush()\n\n"
        f"log_msg(f'Watchdog started. parent={parent_pid}, threshold={danger_threshold_gb} GB, interval={interval_sec} s')\n\n"
        f"while True:\n"
        f"    time.sleep({interval_sec})\n"
        f"    if not __import__('pathlib').Path(f'/proc/{parent_pid}').exists():\n"
        f"        log_msg('Parent PID {parent_pid} no longer exists. Exiting.')\n"
        f"        break\n"
        f"    avail = available_memory_gb()\n"
        f"    if avail >= {danger_threshold_gb}:\n"
        f"        continue\n"
        f"    log_msg(f'DANGER: {{avail:.1f}} GB available (threshold={danger_threshold_gb} GB). Killing subprocesses...')\n"
        f"    freed = kill_heaviest_processes({parent_pid}, max_gb_to_free=100, logger=log_msg)\n"
        f"    if freed > 0:\n"
        f"        log_msg(f'Freed {{freed:.1f}} GB, now {{available_memory_gb():.1f}} GB available')\n"
        f"    else:\n"
        f"        log_msg(f'No child processes to kill. Still {{avail:.1f}} GB available.')\n"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(project_root)
    return subprocess.Popen(
        [sys.executable, "-c", script],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
