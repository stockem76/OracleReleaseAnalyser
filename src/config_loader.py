"""
config_loader.py
----------------
Loads config/settings.yaml relative to the project root.
Returns a plain dict; no validation framework required.
"""

from pathlib import Path
import yaml

# Project root is two levels up from this file (src/config_loader.py → project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_config(path: str | None = None) -> dict:
    """Load and return the settings YAML as a plain dict.

    Parameters
    ----------
    path:
        Optional explicit path to a YAML config file.
        Defaults to ``<project_root>/config/settings.yaml``.
    """
    config_path = Path(path) if path else _PROJECT_ROOT / "config" / "settings.yaml"
    with config_path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)
