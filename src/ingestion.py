"""
ingestion.py
------------
Oracle release notes ingestion layer.

Supports three ingestion modes:
  1. URL   — fetches an Oracle readiness HTML page and parses change items
  2. CSV   — reads a structured CSV export of release changes
  3. XLSX  — reads a structured Excel export of release changes

All modes normalise their output to a list of dicts matching the
Release_Changes schema, then write to the Oracle_Releases and
Release_Changes sheets in the workbook.

Usage (CLI via main.py --ingest-url / --ingest-csv / --ingest-xlsx)
or programmatically:

    from src.ingestion import ingest_url, ingest_csv, ingest_xlsx

    rows = ingest_url("https://www.oracle.com/a1000644/")
    rows = ingest_csv("data/release_changes.csv")
    rows = ingest_xlsx("data/release_changes.xlsx")

Each returns a list of dicts with keys matching Release_Changes columns.
"""

from __future__ import annotations

import csv
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Column schema for Release_Changes (used for normalisation)
# ---------------------------------------------------------------------------

RELEASE_CHANGE_COLUMNS = [
    "Change_ID", "Release_ID", "Change_Title", "Change_Description",
    "Oracle_Module", "Feature_Area", "Change_Type", "Technical_Object",
    "API_Service", "Config_Area", "Security_Flag", "Compliance_Flag",
    "Deprecation_Flag", "Required_Action", "Oracle_Severity",
    "Effective_Date", "Source_Reference", "Source_Section",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_change_id() -> str:
    return f"CHG_{uuid.uuid4().hex[:8].upper()}"


def _today() -> str:
    return date.today().isoformat()


def _clean(val: Any) -> str:
    """Strip whitespace from a value and return empty string if None."""
    if val is None:
        return ""
    return str(val).strip()


def _normalise_row(raw: dict, release_id: str) -> dict:
    """Map a raw dict (any key casing) to the Release_Changes schema."""
    # Build a lowercase lookup so we tolerate any key casing from the source
    lc = {k.lower().strip(): v for k, v in raw.items()}

    def get(*candidates) -> str:
        for key in candidates:
            if key in lc:
                return _clean(lc[key])
        return ""

    return {
        "Change_ID":          get("change_id", "id", "change id") or _new_change_id(),
        "Release_ID":         release_id,
        "Change_Title":       get("change_title", "title", "feature", "subject"),
        "Change_Description": get("change_description", "description", "detail", "summary"),
        "Oracle_Module":      get("oracle_module", "module", "product area"),
        "Feature_Area":       get("feature_area", "feature area", "area"),
        "Change_Type":        get("change_type", "type", "update type"),
        "Technical_Object":   get("technical_object", "object", "technical object"),
        "API_Service":        get("api_service", "api", "service"),
        "Config_Area":        get("config_area", "configuration area"),
        "Security_Flag":      get("security_flag", "security"),
        "Compliance_Flag":    get("compliance_flag", "compliance"),
        "Deprecation_Flag":   get("deprecation_flag", "deprecated", "deprecation"),
        "Required_Action":    get("required_action", "action required", "action"),
        "Oracle_Severity":    get("oracle_severity", "severity", "impact level"),
        "Effective_Date":     get("effective_date", "date", "release date"),
        "Source_Reference":   get("source_reference", "reference", "doc id"),
        "Source_Section":     get("source_section", "section"),
    }


# ---------------------------------------------------------------------------
# Ingestion: CSV
# ---------------------------------------------------------------------------

def ingest_csv(path: str, release_id: str = "") -> list[dict]:
    """Read a CSV file and return normalised Release_Changes rows.

    The CSV must have a header row. Column names are matched
    case-insensitively against the Release_Changes schema.
    """
    release_id = release_id or f"REL_{_today()}"
    rows: list[dict] = []

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for raw in reader:
            rows.append(_normalise_row(raw, release_id))

    return rows


# ---------------------------------------------------------------------------
# Ingestion: XLSX
# ---------------------------------------------------------------------------

def ingest_xlsx(path: str, release_id: str = "", sheet_name: str | None = None) -> list[dict]:
    """Read an Excel file and return normalised Release_Changes rows.

    The first (or named) sheet must have a header row in row 1.
    Column names are matched case-insensitively.
    """
    try:
        from openpyxl import load_workbook as _load_wb
    except ImportError as exc:
        raise ImportError("openpyxl is required for XLSX ingestion.") from exc

    release_id = release_id or f"REL_{_today()}"
    wb = _load_wb(path, read_only=True, data_only=True)
    ws = wb[sheet_name] if sheet_name else wb.active

    rows_iter = ws.iter_rows(values_only=True)
    headers = [str(h).strip() if h is not None else "" for h in next(rows_iter)]

    result: list[dict] = []
    for row in rows_iter:
        raw = dict(zip(headers, row))
        result.append(_normalise_row(raw, release_id))

    wb.close()
    return result


# ---------------------------------------------------------------------------
# Ingestion: URL (HTML)
# ---------------------------------------------------------------------------

def ingest_url(url: str, release_id: str = "") -> list[dict]:
    """Fetch an Oracle readiness HTML page and parse change items.

    Looks for <table> elements (common in Oracle readiness pages) and
    treats the first table with recognisable column headers as the
    change log. Falls back to <li> bullet parsing when no table found.

    Requires: pip install requests beautifulsoup4 lxml
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise ImportError(
            "URL ingestion requires 'requests' and 'beautifulsoup4'.\n"
            "  pip install requests beautifulsoup4 lxml"
        ) from exc

    release_id = release_id or f"REL_{_today()}"

    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        raise SystemExit(
            f"\nERROR: Could not fetch URL — {exc}\n"
            "Check the URL is a valid Oracle readiness or What's New page.\n"
            "Example: https://www.oracle.com/webfolder/technetwork/tutorials/tutorial/readiness/offering.html"
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise SystemExit(f"\nERROR: Network connection failed — {exc}") from exc

    soup = BeautifulSoup(resp.text, "lxml")

    # Try table-based parsing first
    rows = _parse_html_tables(soup, release_id)
    if rows:
        return rows

    # Fallback: parse bullet-list items as plain change descriptions
    return _parse_html_bullets(soup, release_id)


def _parse_html_tables(soup, release_id: str) -> list[dict]:
    """Extract rows from the first <table> with a usable header row."""
    for table in soup.find_all("table"):
        header_row = table.find("tr")
        if not header_row:
            continue
        headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
        if not headers:
            continue

        result: list[dict] = []
        for tr in table.find_all("tr")[1:]:
            cells = [td.get_text(separator=" ", strip=True) for td in tr.find_all(["td", "th"])]
            if not any(cells):
                continue
            raw = dict(zip(headers, cells))
            result.append(_normalise_row(raw, release_id))

        if result:
            return result

    return []


def _parse_html_bullets(soup, release_id: str) -> list[dict]:
    """Fallback: treat each <li> as a separate change description."""
    result: list[dict] = []
    for li in soup.find_all("li"):
        text = li.get_text(separator=" ", strip=True)
        if len(text) < 20:  # skip trivial nav items
            continue
        result.append({
            "Change_ID":          _new_change_id(),
            "Release_ID":         release_id,
            "Change_Title":       text[:120],
            "Change_Description": text,
            "Oracle_Module":      "",
            "Feature_Area":       "",
            "Change_Type":        "",
            "Technical_Object":   "",
            "API_Service":        "",
            "Config_Area":        "",
            "Security_Flag":      "",
            "Compliance_Flag":    "",
            "Deprecation_Flag":   "",
            "Required_Action":    "",
            "Oracle_Severity":    "",
            "Effective_Date":     _today(),
            "Source_Reference":   "",
            "Source_Section":     "",
        })
    return result


# ---------------------------------------------------------------------------
# Write parsed rows into the workbook
# ---------------------------------------------------------------------------

def write_to_workbook(wb, rows: list[dict], release_id: str, release_meta: dict | None = None) -> None:
    """Write normalised ingestion rows into Oracle_Releases and Release_Changes.

    Parameters
    ----------
    wb:           The openpyxl Workbook to write into.
    rows:         Normalised rows from ingest_csv / ingest_xlsx / ingest_url.
    release_id:   The Release_ID to stamp on the Oracle_Releases sheet.
    release_meta: Optional dict with keys: Release_Name, Release_Year,
                  Release_Quarter, Oracle_Product, Release_Date,
                  Notes_Source_URL.  Sensible defaults are used if omitted.
    """
    today = _today()
    meta = release_meta or {}

    # --- Oracle_Releases row ---
    rel_ws = wb["Oracle_Releases"]
    # Find next empty row (after header)
    next_row = _next_empty_row(rel_ws)
    rel_ws.cell(next_row, 1, release_id)
    rel_ws.cell(next_row, 2, meta.get("Release_Name", release_id))
    rel_ws.cell(next_row, 3, meta.get("Release_Year", ""))
    rel_ws.cell(next_row, 4, meta.get("Release_Quarter", ""))
    rel_ws.cell(next_row, 5, meta.get("Oracle_Product", ""))
    rel_ws.cell(next_row, 6, meta.get("Release_Date", today))
    rel_ws.cell(next_row, 7, meta.get("Notes_Source_URL", ""))
    rel_ws.cell(next_row, 8, today)
    rel_ws.cell(next_row, 9, "Active")

    # --- Release_Changes rows ---
    chg_ws = wb["Release_Changes"]
    next_row = _next_empty_row(chg_ws)
    cols = RELEASE_CHANGE_COLUMNS
    for r_offset, row in enumerate(rows):
        for c_idx, col in enumerate(cols, start=1):
            chg_ws.cell(next_row + r_offset, c_idx, row.get(col, ""))


def _next_empty_row(ws) -> int:
    """Return the first row index where column A is empty (after header)."""
    for r_idx, row in enumerate(ws.iter_rows(min_row=2, max_col=1, values_only=True), start=2):
        if row[0] is None:
            return r_idx
    return (ws.max_row or 1) + 1
