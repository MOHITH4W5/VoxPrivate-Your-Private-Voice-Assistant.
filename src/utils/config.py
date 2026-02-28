"""
src/utils/config.py
Loads config.yaml and provides easy attribute access.
"""

import yaml
import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def load_config(path: str = None) -> dict:
    """Load config.yaml from the project root."""
    if path is None:
        path = ROOT_DIR / "config.yaml"
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data


class Config:
    """Simple config accessor wrapping a dict."""

    def __init__(self, config_dict: dict):
        self._data = config_dict

    def get(self, *keys, default=None):
        """Nested key access: config.get('audio', 'sample_rate')"""
        val = self._data
        for k in keys:
            if not isinstance(val, dict):
                return default
            val = val.get(k, default)
        return val

    @classmethod
    def from_file(cls, path: str = None) -> "Config":
        return cls(load_config(path))

    def __repr__(self):
        return f"Config({self._data})"
