"""
main.py
-------
Entrypoint for the Oracle Fusion Impact Analyzer.

Orchestrates all builder modules in the correct dependency order and
writes the finished workbook to the configured output path.

Usage
-----
    # From the project root:
    python src/main.py                   # uses config/settings.yaml
    python src/main.py path/to/cfg.yaml  # uses a custom config file

    # Or from anywhere:
    python -m src.main

Programmatic
------------
    from src.main import generate
    generate()                           # or generate(config_path="...")
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime
from pathlib import Path

# Ensure the project root (parent of this file's directory) is on sys.path
# so that `from src.X import ...` works regardless of the working directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
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
from src.seed_data import seed_all


def _build_instructions(wb) -> None:
    """Write guidance content to the Instructions sheet."""
    ws = wb["Instructions"]
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 80

    title_cell = ws["A1"]
    title_cell.value = "Oracle Fusion Impact Analyzer — Enterprise Edition"
    title_cell.font = Font(size=16, bold=True)

    ws.merge_cells("A1:B1")

    rows = [
        ("", ""),
        ("Purpose",
         "This workbook supports Oracle Fusion quarterly release impact assessment, "
         "governance, migration, testing, integration lineage, and operational readiness."),
        ("", ""),
        ("How to use", ""),
        ("1. Clients",          "Register each client or business unit being assessed."),
        ("2. Oracle_Releases",  "Record Oracle quarterly releases to be assessed."),
        ("3. Release_Changes",  "Populate or import Oracle release note changes."),
        ("4. Business_Processes", "Register in-scope business processes per module."),
        ("5. Applications",     "List all applications and integrations in scope."),
        ("6. Configurations",   "Document key configuration items that may be impacted."),
        ("7. Customizations",   "List customizations, extensions, and CEMLI objects."),
        ("8. Controls",         "Register SOX or operational controls to be re-tested."),
        ("9. Test_Cases",       "Maintain the test case library linked to release changes."),
        ("10. Impact_Assessments",
         "Core analysis table. Risk scores are calculated automatically via formula. "
         "Set Client_ID and Release_ID to filter the Executive Summary."),
        ("11. Remediation_Actions", "Track remediation tasks arising from impact assessments."),
        ("12. RAID_Log",        "Log Risks, Assumptions, Issues, and Dependencies."),
        ("13. Testing_Command_Centre", "Track test execution runs and defect links."),
        ("14. Defect_Analytics","Categorise and analyse defects found during testing."),
        ("15. Release_Readiness","Record go/no-go readiness status per domain."),
        ("16. Integration_Topology", "Map all integration connections and their criticality."),
        ("17. OTBI_Inventory",  "Inventory of OTBI reports that may be affected by changes."),
        ("18. BIP_Reports",     "Inventory of BI Publisher reports in scope."),
        ("19. HDL_FBDI_Loads",  "Track HCM Data Loader and FBDI file-based load jobs."),
        ("20. Security_Roles",  "Document Oracle security roles and access levels."),
        ("21. Environment_Promotions", "Track promotion history across environments."),
        ("22. Cutover_Runbook", "Step-by-step cutover sequence for go-live."),
        ("23. AI_Governance",   "Govern AI models used in analysis — approval and audit log."),
        ("24. Approval_Workflow","Record approval decisions for governed artefacts."),
        ("25. Deployment_Status","Track deployment status of components per release."),
        ("26. Executive_Summary",
         "Dashboard with KPI counts and risk distribution chart. "
         "Enter Client_ID in B3 and Release_ID in B4 to filter."),
        ("", ""),
        ("Governed sheets",
         "Reference_Lists, Scoring_Rules, Metadata_Config, Data_Lineage, and "
         "PowerQuery_Control are protected. Contact the workbook owner to amend them."),
        ("", ""),
        ("Support",             "Internal enterprise use only. Confidential."),
    ]

    # Style the section label cells in column A
    label_font = Font(bold=True)

    for r_idx, (label, value) in enumerate(rows, start=2):
        a = ws.cell(row=r_idx, column=1, value=label)
        b = ws.cell(row=r_idx, column=2, value=value)
        b.alignment = Alignment(wrap_text=True, vertical="top")
        if label and not label[0].isdigit() and label not in ("", "How to use"):
            a.font = label_font
        if label == "How to use":
            a.font = Font(bold=True, underline="single")
        ws.row_dimensions[r_idx].height = 18

    ws.sheet_view.showGridLines = False


def generate(
    config_path: str | None = None,
    output: str | None = None,
    seed: bool = True,
    ingest_csv: str | None = None,
    ingest_xlsx: str | None = None,
    ingest_url: str | None = None,
    release_id: str | None = None,
    client_id: str | None = None,
) -> Path:
    """Build and save the workbook.  Returns the resolved output path.

    Parameters
    ----------
    config_path: Path to settings YAML (default: config/settings.yaml).
    output:      Override the output file path from config.
    seed:        If True, populate sheets with demo data (default: True).
    ingest_csv:  Path to a CSV file to ingest into Release_Changes.
    ingest_xlsx: Path to an XLSX file to ingest into Release_Changes.
    ingest_url:  URL of an Oracle readiness page to scrape.
    release_id:  Release_ID to stamp on ingested rows (default: auto).
    client_id:   Unused in generation; reserved for future filtering.
    """

    # 1. Load config
    cfg = load_config(config_path)
    if output:
        cfg["output_file"] = output

    # 2. Initialise styles (must happen before any sheet builder is called)
    styles.init_styles(cfg)

    # 3. Build workbook skeleton (sheets + tables + headers)
    wb = build_workbook(cfg)

    # 4. Seed Reference_Lists + register DefinedNames
    populate_reference_lists(wb, cfg)

    # 5. Seed demo data (after tables/validation, before formulas so
    #    formula cells in cols R/T/U are written last and not overwritten)
    if seed:
        seed_all(wb)

    # 6. Apply DataValidation dropdowns
    apply_validations(wb, cfg)

    # 7. Inject formulas
    apply_formulas(wb, cfg)

    # 8. Apply conditional formatting
    apply_conditional_formatting(wb, cfg)

    # 8. Build Executive Summary dashboard + chart
    build_executive_summary(wb)

    # 8b. Build Instructions sheet
    _build_instructions(wb)

    # 8c. Ingest release notes if requested
    if ingest_csv or ingest_xlsx or ingest_url:
        from src.ingestion import ingest_csv as _ingest_csv
        from src.ingestion import ingest_xlsx as _ingest_xlsx
        from src.ingestion import ingest_url as _ingest_url
        from src.ingestion import write_to_workbook

        rid = release_id or ""
        if ingest_csv:
            rows = _ingest_csv(ingest_csv, rid)
            write_to_workbook(wb, rows, rid or "REL_CSV")
            print(f"Ingested {len(rows)} rows from CSV: {ingest_csv}")
        if ingest_xlsx:
            rows = _ingest_xlsx(ingest_xlsx, rid)
            write_to_workbook(wb, rows, rid or "REL_XLSX")
            print(f"Ingested {len(rows)} rows from XLSX: {ingest_xlsx}")
        if ingest_url:
            rows = _ingest_url(ingest_url, rid)
            write_to_workbook(wb, rows, rid or "REL_URL")
            print(f"Ingested {len(rows)} rows from URL: {ingest_url}")

    # 9. Stamp Metadata_Config
    meta_ws = wb["Metadata_Config"]
    meta_ws["A1"] = "Generated_Date"
    meta_ws["B1"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_ws["A2"] = "Workbook_ID"
    meta_ws["B2"] = str(uuid.uuid4())
    meta_ws["A3"] = "Version"
    meta_ws["B3"] = "1.0"

    # 10. Add governing comment to Impact_Assessments
    wb["Impact_Assessments"]["A1"].comment = Comment(
        "Enterprise Oracle Fusion quarterly impact analysis table.",
        "Oracle Enterprise Architecture",
    )

    # 11. Apply sheet protection + cell locking (must be last before save)
    apply_protection(wb, cfg)

    # 12. Resolve output path and save
    # cfg["output_file"] may be relative (e.g. "output/foo.xlsx") — resolve
    # it relative to the project root, not the current working directory.
    project_root = Path(__file__).resolve().parent.parent
    output_path = (project_root / cfg["output_file"]).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        wb.save(output_path)
    except PermissionError:
        raise SystemExit(
            f"\nERROR: Cannot write to '{output_path}'.\n"
            "The file is open in another application (e.g. Excel).\n"
            "Close it and re-run."
        )
    print(f"Workbook saved: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser():
    import argparse
    p = argparse.ArgumentParser(
        prog="python src/main.py",
        description="Oracle Fusion Impact Analyzer — Enterprise Edition",
    )
    p.add_argument(
        "--config", "-c",
        metavar="PATH",
        default=None,
        help="Path to settings YAML (default: config/settings.yaml)",
    )
    p.add_argument(
        "--output", "-o",
        metavar="PATH",
        default=None,
        help="Override output .xlsx file path",
    )
    p.add_argument(
        "--no-seed",
        action="store_true",
        default=False,
        help="Skip seeding demo data into the workbook",
    )
    p.add_argument(
        "--release", "-r",
        metavar="RELEASE_ID",
        default=None,
        help="Release_ID to stamp on ingested rows (e.g. REL_24C)",
    )
    p.add_argument(
        "--client",
        metavar="CLIENT_ID",
        default=None,
        help="Client_ID context (reserved for future filtering)",
    )
    p.add_argument(
        "--ingest-csv",
        metavar="PATH",
        default=None,
        help="Ingest release changes from a CSV file",
    )
    p.add_argument(
        "--ingest-xlsx",
        metavar="PATH",
        default=None,
        help="Ingest release changes from an XLSX file",
    )
    p.add_argument(
        "--ingest-url",
        metavar="URL",
        default=None,
        help="Ingest release changes from an Oracle readiness HTML page",
    )
    return p


if __name__ == "__main__":
    parser = _build_parser()
    args = parser.parse_args()
    generate(
        config_path=args.config,
        output=args.output,
        seed=not args.no_seed,
        ingest_csv=args.ingest_csv,
        ingest_xlsx=args.ingest_xlsx,
        ingest_url=args.ingest_url,
        release_id=args.release,
        client_id=args.client,
    )
