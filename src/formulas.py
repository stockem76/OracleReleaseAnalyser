"""
formulas.py
-----------
Injects Excel formulas and conditional formatting rules into the
Impact_Assessments sheet.
"""

from openpyxl.formatting.rule import FormulaRule
from src.styles import CRITICAL_FILL, HIGH_FILL, MEDIUM_FILL, LOW_FILL


def apply_formulas(wb, config: dict) -> None:
    """Write risk-scoring formulas into Impact_Assessments rows 2–max_rows."""
    max_rows = config["max_rows"]
    ws = wb["Impact_Assessments"]

    for row in range(2, max_rows + 1):
        # Col R — Oracle severity score via XLOOKUP
        ws[f"R{row}"] = (
            "=IFERROR("
            "XLOOKUP("
            f"XLOOKUP(D{row},tblReleaseChanges[Change_ID],"
            'tblReleaseChanges[Oracle_Severity],""),'
            "tblSeverityMap[Severity_Text],"
            "tblSeverityMap[Score],0),0)"
        )

        # Col T — weighted total risk score
        ws[f"T{row}"] = (
            "=ROUND(("
            f"M{row}*0.25)+"
            f"(N{row}*0.20)+"
            f"(O{row}*0.15)+"
            f"(P{row}*0.15)+"
            f"(Q{row}*0.10)+"
            f"(R{row}*0.10)+"
            f"(S{row}*0.05),2)"
        )

        # Col U — Risk Level label derived from total score
        ws[f"U{row}"] = (
            f'=IF(T{row}>=4.25,"Critical",'
            f'IF(T{row}>=3.5,"High",'
            f'IF(T{row}>=2,"Medium","Low")))'
        )


def apply_conditional_formatting(wb, config: dict) -> None:  # noqa: ARG001
    """Apply colour-coded conditional formatting to Risk_Level column U."""
    ws = wb["Impact_Assessments"]
    max_rows = config["max_rows"]
    range_ref = f"U2:U{max_rows}"

    ws.conditional_formatting.add(
        range_ref, FormulaRule(formula=['U2="Critical"'], fill=CRITICAL_FILL)
    )
    ws.conditional_formatting.add(
        range_ref, FormulaRule(formula=['U2="High"'], fill=HIGH_FILL)
    )
    ws.conditional_formatting.add(
        range_ref, FormulaRule(formula=['U2="Medium"'], fill=MEDIUM_FILL)
    )
    ws.conditional_formatting.add(
        range_ref, FormulaRule(formula=['U2="Low"'], fill=LOW_FILL)
    )
