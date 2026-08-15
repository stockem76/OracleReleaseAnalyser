"""
generate_dfl.py
---------------
Generate the DFL (Dignity Funerals Limited) Oracle Fusion 26C Impact Assessment workbook.

Usage
-----
    py generate_dfl.py

Output
------
    output/DFL_Oracle_26C_Impact_Assessment.xlsx
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font

from src.config_loader import load_config
from src import styles
from src.sheets import build_workbook
from src.reference_lists import populate_reference_lists
from src.validation import apply_validations
from src.formulas import apply_formulas, apply_conditional_formatting
from src.charts import build_executive_summary
from src.protection import apply_protection
from src.dfl_seed import seed_dfl


def _build_dfl_instructions(wb) -> None:
    ws = wb["Instructions"]
    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 85

    title = ws["A1"]
    title.value = "Oracle Fusion 26C Impact Assessment — Dignity Funerals Limited (DFL)"
    title.font = Font(size=16, bold=True)
    ws.merge_cells("A1:B1")

    rows = [
        ("", ""),
        ("Client",            "Dignity Funerals Limited (DFL) — Sutton Coldfield HQ"),
        ("Release",           "Oracle Fusion Cloud 26C — Target go-live: September 2025"),
        ("Prepared",          f"{datetime.now().strftime('%d %B %Y')}"),
        ("Scope",             "Oracle ERP (Financials, Procurement, Project Mgmt), HCM (Payroll, HR, Absence, "
                              "Time & Labour, Benefits, Compensation, Recruiting, Workforce Scheduling), "
                              "SCM (Inventory Management, Order Management)"),
        ("", ""),
        ("Business Context",  "DFL operates ~500 funeral homes across the UK with ~4,200 employees. "
                              "Oracle Fusion Cloud is the core ERP/HCM platform supporting payroll, "
                              "HR, finance, and supply chain for funeral supplies and services."),
        ("", ""),
        ("Critical Changes",  ""),
        ("1. SOAP API Deprecation", "Fixed Assets SOAP API deprecated — MUST migrate to REST before 27A."),
        ("2. Payroll Legislation",  "UK payroll run results archive enhanced for NI/minimum wage changes — "
                                    "parallel payroll testing mandatory."),
        ("3. OM REST API",          "Order Management REST API schema changes affect funeral case management "
                                    "system integration."),
        ("4. GL Period Close",      "General Ledger period close migrated to Redwood — finance team retraining required."),
        ("5. HR API Change",        "HCM Workers REST API v2 introduces new required field affecting HR reporting integration."),
        ("", ""),
        ("How To Use",        ""),
        ("Impact_Assessments","Core analysis table. 21 change assessments pre-loaded for DFL."),
        ("Release_Changes",   "Full list of 26C changes in scope for DFL (ERP + HCM + SCM)."),
        ("Remediation_Actions","Tracked remediation tasks for Critical/High items."),
        ("Test_Cases",        "Test cases linked to assessed changes — use for UAT planning."),
        ("Executive_Summary", "KPI dashboard. Enter CLT_DFL001 in B3 and REL_26C in B4 to filter."),
        ("", ""),
        ("Governance",        "This workbook is CONFIDENTIAL. Internal use only."),
    ]

    label_font = Font(bold=True)
    for r_idx, (label, value) in enumerate(rows, start=2):
        a = ws.cell(row=r_idx, column=1, value=label)
        b = ws.cell(row=r_idx, column=2, value=value)
        b.alignment = Alignment(wrap_text=True, vertical="top")
        if label and not label[0].isdigit() and label not in ("", "How To Use", "Critical Changes"):
            a.font = label_font
        if label in ("How To Use", "Critical Changes"):
            a.font = Font(bold=True, underline="single")
        ws.row_dimensions[r_idx].height = 18

    ws.sheet_view.showGridLines = False


def generate_dfl():
    cfg = load_config()
    cfg["output_file"] = "output/DFL_Oracle_26C_Impact_Assessment.xlsx"

    styles.init_styles(cfg)
    wb = build_workbook(cfg)
    populate_reference_lists(wb, cfg)

    # DFL-specific seed (no generic demo data)
    seed_dfl(wb)

    apply_validations(wb, cfg)
    apply_formulas(wb, cfg)
    apply_conditional_formatting(wb, cfg)
    build_executive_summary(wb)
    _build_dfl_instructions(wb)

    # Stamp metadata
    meta = wb["Metadata_Config"]
    meta["A1"] = "Generated_Date"
    meta["B1"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta["A2"] = "Workbook_ID"
    meta["B2"] = str(uuid.uuid4())
    meta["A3"] = "Version"
    meta["B3"] = "1.0"
    meta["A4"] = "Client"
    meta["B4"] = "Dignity Funerals Limited (DFL)"
    meta["A5"] = "Release"
    meta["B5"] = "Oracle Fusion 26C"

    wb["Impact_Assessments"]["A1"].comment = Comment(
        "DFL Oracle Fusion 26C impact assessment — 21 in-scope changes.",
        "Oracle Enterprise Architecture",
    )

    apply_protection(wb, cfg)

    project_root = Path(__file__).resolve().parent
    output_path = (project_root / cfg["output_file"]).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        wb.save(output_path)
    except PermissionError:
        raise SystemExit(
            f"\nERROR: Cannot write to '{output_path}'.\n"
            "Close the file in Excel and re-run."
        )

    # Count total impacts from JSON if present
    import json as _json
    _impacts_path = project_root / "dfl_26c_impacts.json"
    _impact_count = 0
    if _impacts_path.exists():
        try:
            with open(_impacts_path, encoding="utf-8") as fh:
                raw = fh.read()
                if raw and raw[0] == "\ufeff":
                    raw = raw[1:]
                _impact_count = len(_json.loads(raw))
        except Exception:
            pass

    print(f"\nDFL 26C Impact Assessment workbook saved:")
    print(f"  {output_path}")
    print(f"\nSummary:")
    print(f"  Client:   Dignity Funerals Limited (DFL)")
    print(f"  Release:  Oracle Fusion 26C")
    from src.dfl_seed import _CHANGES as _curated
    _curated_count = len(_curated)
    print(f"  Curated changes:       {_curated_count} (CHG_PAY_*, CHG_HR_*, CHG_FIN_*, CHG_OM_* etc.)")
    if _impact_count:
        print(f"  MCP-sourced impacts:   {_impact_count} (CHG_IMP_* / ASMT_IMP_*)")
        print(f"  Total Release_Changes: {_curated_count + _impact_count}")
    print(f"  Critical: CHG_FIN_003 (SOAP API deprecation), CHG_PAY_002 (UK payroll legislation)")
    print(f"  High:     CHG_HR_001, CHG_HR_002, CHG_ABS_002, CHG_FIN_002, CHG_FIN_004, CHG_OM_001")
    return output_path


if __name__ == "__main__":
    generate_dfl()
