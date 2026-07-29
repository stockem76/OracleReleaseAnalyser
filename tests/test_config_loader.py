"""Tests for src/config_loader.py"""

from src.config_loader import load_config


def test_load_config_returns_dict():
    cfg = load_config()
    assert isinstance(cfg, dict)


def test_max_rows_is_int():
    cfg = load_config()
    assert isinstance(cfg["max_rows"], int)
    assert cfg["max_rows"] > 0


def test_output_file_is_str():
    cfg = load_config()
    assert isinstance(cfg["output_file"], str)
    assert cfg["output_file"].endswith(".xlsx")


def test_column_width_is_int():
    cfg = load_config()
    assert isinstance(cfg["column_width"], int)


def test_colours_present():
    cfg = load_config()
    colours = cfg["colours"]
    for key in ("header_fill", "critical", "high", "medium", "low"):
        assert key in colours
        assert isinstance(colours[key], str)
