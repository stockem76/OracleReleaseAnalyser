"""Tests for src/styles.py"""

from src.config_loader import load_config
from src import styles


def _cfg():
    return load_config()


def test_init_styles_sets_all_objects():
    styles.init_styles(_cfg())
    assert styles.HEADER_FILL is not None
    assert styles.HEADER_FONT is not None
    assert styles.CENTER is not None
    assert styles.THIN_BORDER is not None
    assert styles.CRITICAL_FILL is not None
    assert styles.HIGH_FILL is not None
    assert styles.MEDIUM_FILL is not None
    assert styles.LOW_FILL is not None


def test_header_fill_colour():
    cfg = _cfg()
    styles.init_styles(cfg)
    assert styles.HEADER_FILL.fgColor.rgb.upper().endswith(
        cfg["colours"]["header_fill"].upper()
    )


def test_critical_fill_colour():
    cfg = _cfg()
    styles.init_styles(cfg)
    assert styles.CRITICAL_FILL.fgColor.rgb.upper().endswith(
        cfg["colours"]["critical"].upper()
    )


def test_style_header_applies_fill(tmp_path):
    from openpyxl import Workbook

    styles.init_styles(_cfg())
    wb = Workbook()
    ws = wb.active
    cell = ws["A1"]
    styles.style_header(cell)
    assert cell.fill.fgColor.rgb == styles.HEADER_FILL.fgColor.rgb
    assert cell.font.bold is True
