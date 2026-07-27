"""
Configuration utilities for fertility_popEVE.
"""

import os
import re
import shutil
from pathlib import Path

import yaml

DEFAULT_CONFIG = "config/config.yaml"
EXAMPLE_CONFIG = "config/config.example.yaml"


def _resolve_env_vars(value):  # noqa: C901
    """Recursively expand ``${VAR:default}`` in string values."""
    if isinstance(value, str):
        pattern = re.compile(r"\$\{(\w+):([^}]*)\}")
        return pattern.sub(
            lambda m: os.environ.get(m.group(1), m.group(2)) or "",
            value,
        )
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(v) for v in value]
    return value


def load_config(config_file: str = DEFAULT_CONFIG) -> dict:
    """
    Load configuration from YAML.

    Resolves ``${ENV_VAR:default}`` placeholders in string values.

    If ``config/config.yaml`` is missing (fresh clone), copies
    ``config/config.example.yaml`` as a starting point and warns.
    """

    config_path = Path(config_file)

    if not config_path.is_file():
        example = Path(EXAMPLE_CONFIG)
        if example.is_file():
            print(
                f"[CONFIG] {config_path} not found — "
                f"copying {EXAMPLE_CONFIG} as starting template. "
                f"Edit config paths before running the pipeline."
            )
            shutil.copy2(example, config_path)
        else:
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}"
            )

    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return _resolve_env_vars(config)
