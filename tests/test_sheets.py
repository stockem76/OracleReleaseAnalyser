"""Tests for src/sheets.py"""

from src.config_loader import load_config
from src import styles
from src.sheets import build_workbook, SHEET_ORDER, TABLES, PLAIN_HEADERS


def _build():
    cfg = load_config()
    styles.init_styles(cfg)
    return build_workbook(cfg), cfg


def test_all_sheets_present():
    wb, _ = _build()
    for name in SHEET_ORDER:
        assert name in wb.sheetnames, f"Missing sheet: {name}"


def test_sheet_count():
    wb, _ = _build()
    assert len(wb.sheetnames) >= 40


def test_table_sheets_have_headers():
    wb, cfg = _build()
    for sheet_name, table_cfg in TABLES.items():
        ws = wb[sheet_name]
        for idx, col_name in enumerate(table_cfg["columns"], start=1):
            assert ws.cell(row=1, column=idx).value == col_name


def test_plain_header_sheets_have_headers():
    wb, _ = _build()
    for sheet_name, headers in PLAIN_HEADERS.items():
        ws = wb[sheet_name]
        for idx, h in enumerate(headers, start=1):
            assert ws.cell(row=1, column=idx).value == h


def test_freeze_panes_set_on_table_sheets():
    wb, _ = _build()
    for sheet_name in TABLES:
        ws = wb[sheet_name]
        assert ws.freeze_panes == "A2"
