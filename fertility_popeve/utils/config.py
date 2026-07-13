"""
Configuration utilities for fertility_popEVE.
"""

from pathlib import Path

import yaml

DEFAULT_CONFIG = "config/config.yaml"


def load_config(config_file: str = DEFAULT_CONFIG) -> dict:
    """
    Load configuration from YAML.
    """

    config_path = Path(config_file)

    if not config_path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config
