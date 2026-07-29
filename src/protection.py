"""
protection.py
-------------
Applies workbook sheet protection and locks formula cells in the
Impact_Assessments sheet.
"""

from openpyxl.styles import Protection

_PROTECTED_TABS = [
    "Scoring_Rules",
    "Reference_Lists",
    "Metadata_Config",
    "Data_Lineage",
    "PowerQuery_Control",
]

# Columns in Impact_Assessments that contain generated formulas and
# should be locked against accidental editing (1-based: R=18, T=20, U=21)
_FORMULA_COLS = (18, 20, 21)


def apply_protection(wb, config: dict) -> None:
    """Lock governed sheets and formula cells in Impact_Assessments."""
    # Sheet-level protection
    for tab in _PROTECTED_TABS:
        wb[tab].protection.sheet = True

    # Cell-level locking for formula columns in Impact_Assessments
    max_rows = config["max_rows"]
    ws = wb["Impact_Assessments"]
    for col in _FORMULA_COLS:
        for row in ws.iter_rows(
            min_row=2, max_row=max_rows, min_col=col, max_col=col
        ):
            for cell in row:
                cell.protection = Protection(locked=True)
