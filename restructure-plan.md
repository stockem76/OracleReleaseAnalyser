# Oracle Fusion Impact Analyzer — Restructure Plan

## Confirmed Decisions

| # | Decision |
|---|---|
| 1 | `run.py` is **deleted** after the integration test passes |
| 2 | Workbook protection and cell-locking go into a dedicated **`src/protection.py`** module |
| 3 | YAML keys use **snake_case** (`max_rows`, `output_file`, `column_width`) |

---

## Overview

The current solution is a single monolithic `run.py` script (~880 lines) that generates an
enterprise Excel workbook using OpenPyXL. The goal is to restructure it into the proper
package layout described in the README:

- A `src/` package split by concern (styles, sheets, formulas, validation, charts)
- A `config/` directory with a `settings.yaml` for all runtime configuration
- A `tests/` directory wired for pytest
- A clean entrypoint at `src/main.py`
- A populated `requirements.txt`
- Supporting scaffolding: `output/`, `logs/`, `data/`, `docs/`

The **behaviour of the generated workbook does not change** — this is purely a structural
refactor. All existing logic from `run.py` is preserved and redistributed into focused modules.

---

## Sub-Tasks

---

### Sub-Task 1 — Scaffold the directory structure and configuration

**Intent**
Create all the directories and files that form the project skeleton. Nothing functional yet —
this establishes the layout every subsequent sub-task builds on.

**Expected Outcomes**
- Directories exist: `src/`, `config/`, `tests/`, `output/`, `logs/`, `data/`, `docs/`
- `config/settings.yaml` contains all current hard-coded constants from `run.py`
  (`output_file`, `max_rows`, all hex colour codes, column widths)
- `requirements.txt` lists `openpyxl`, `pyyaml`, `pytest`, `pytest-cov`
- `src/__init__.py` and `tests/__init__.py` (empty markers) are present
- `run.py` is left untouched at this stage

**Todo List**
1. Create `config/settings.yaml` with keys: `output_file`, `max_rows`, `column_width`,
   `colours.header_fill`, `colours.critical`, `colours.high`, `colours.medium`, `colours.low`
2. Create `requirements.txt` with pinned dependencies
3. Create `src/__init__.py` (empty)
4. Create `tests/__init__.py` (empty)
5. Create empty placeholder files: `output/.gitkeep`, `logs/.gitkeep`, `data/.gitkeep`,
   `docs/.gitkeep`

**Relevant Context**
- Constants to extract from `run.py`: `OUTPUT_FILE` (line 76), `MAX_ROWS` (line 78),
  colour hex values (`1F4E78`, `8B0000`, `FFA500`, `FFFF00`, `90EE90`), `column_width=28`
- README.md specifies the full intended folder layout
- PyYAML will be the YAML loader (`pip install pyyaml`)

**Status** — [x] done

---

### Sub-Task 2 — Create `src/config_loader.py`

**Intent**
Provide a single function that loads `config/settings.yaml` and returns a plain dict.
Every other module imports from here rather than hard-coding values.

**Expected Outcomes**
- `src/config_loader.py` exposes `load_config(path=None) -> dict`
- Default `path` resolves relative to the package root so it works regardless of the
  working directory when `main.py` is called
- A smoke test `tests/test_config_loader.py` asserts the key fields are present and
  of the correct type

**Todo List**
1. Write `load_config()` using `pathlib.Path` to resolve the config file path
2. Load YAML with `yaml.safe_load`
3. Write `tests/test_config_loader.py` — assert `max_rows` is an int, `output_file` is a str

**Relevant Context**
- `config/settings.yaml` created in Sub-Task 1
- Keep it minimal — no validation framework, just a plain dict return

**Status** — [x] done

---

### Sub-Task 3 — Create `src/styles.py`

**Intent**
Extract all OpenPyXL style objects and the `style_header()` helper from `run.py` into a
dedicated module. Every other sheet-building module imports styles from here.

**Expected Outcomes**
- `src/styles.py` exports: `HEADER_FILL`, `HEADER_FONT`, `CENTER`, `THIN_BORDER`,
  `CRITICAL_FILL`, `HIGH_FILL`, `MEDIUM_FILL`, `LOW_FILL`, `style_header(cell)`
- Colour hex values are read from the config dict, not hard-coded
- A smoke test `tests/test_styles.py` instantiates each fill and asserts `.fgColor.rgb`
  matches the config value

**Todo List**
1. Write `src/styles.py` — accept a `config` dict argument to `build_styles(config) -> dict`
   that returns all style objects, OR expose a module-level `init_styles(config)` call
2. Keep `style_header(cell)` as a plain function that references module-level style objects
3. Write `tests/test_styles.py`

**Relevant Context**
- Source lines in `run.py`: 87–144
- Styles must be initialised after config is loaded, since colours come from YAML

**Status** — [x] done

---

### Sub-Task 4 — Create `src/sheets.py`

**Intent**
Extract the workbook creation, sheet ordering, and Excel table definitions from `run.py`.
This module is responsible for building the workbook object with all sheets and their
structured tables.

**Expected Outcomes**
- `src/sheets.py` exposes `build_workbook(config) -> openpyxl.Workbook`
- All 40 sheet names in `sheet_order` are created
- All `TABLES` definitions (Clients, Oracle_Releases, Release_Changes, Impact_Assessments)
  are applied with their column headers, styled headers, column widths, freeze panes,
  and Excel Table objects
- All remaining sheets (AI_Governance, RAID_Log, Testing_Command_Centre, etc.) receive their
  headers via their dedicated header lists
- A smoke test `tests/test_sheets.py` calls `build_workbook(config)` and asserts all expected
  sheet names are present in `wb.sheetnames`

**Todo List**
1. Move `sheet_order` list and `TABLES` dict into `src/sheets.py`
2. Move all per-sheet header definitions (ai_headers, raid_headers, test_headers, etc.) here
3. Implement `build_workbook(config)` that creates the `Workbook`, creates sheets, applies
   tables, headers, and freeze panes
4. Import `style_header` from `src/styles`
5. Write `tests/test_sheets.py`

**Relevant Context**
- Source lines in `run.py`: 150–345 (workbook + tables) and 569–834 (per-sheet headers)
- `MAX_ROWS` should come from `config["max_rows"]`
- `column_width` should come from `config["column_width"]`

**Status** — [x] done

---

### Sub-Task 5 — Create `src/reference_lists.py`

**Intent**
Extract the Reference_Lists seeding and DefinedName creation into its own module.

**Expected Outcomes**
- `src/reference_lists.py` exposes `populate_reference_lists(wb, config)`
- All five named lists (Modules, RiskLevels, Statuses, YesNo, ReviewStatus) are written
  to the `Reference_Lists` sheet
- All five `DefinedName` entries are registered on the workbook

**Todo List**
1. Move the `lists` dict and the population loop from `run.py` lines 353–410
2. Wrap in `populate_reference_lists(wb, config)`
3. No separate test needed here — covered by the integration test in Sub-Task 9

**Relevant Context**
- Source lines in `run.py`: 351–410

**Status** — [x] done

---

### Sub-Task 6 — Create `src/validation.py`

**Intent**
Extract all DataValidation configuration from `run.py` into a focused module.

**Expected Outcomes**
- `src/validation.py` exposes `apply_validations(wb, config)`
- Risk level, review status, and yes/no dropdowns are applied to `Impact_Assessments`
  using the named ranges defined in Sub-Task 5

**Todo List**
1. Move `risk_dv`, `review_dv`, `yesno_dv` setup from `run.py` lines 416–440
2. Wrap in `apply_validations(wb, config)`

**Relevant Context**
- Source lines in `run.py`: 416–440
- Depends on `Reference_Lists` named ranges being present (populated in Sub-Task 5)

**Status** — [x] done

---

### Sub-Task 7 — Create `src/formulas.py`

**Intent**
Extract all formula injection and conditional formatting rules from `run.py` into a
dedicated module.

**Expected Outcomes**
- `src/formulas.py` exposes `apply_formulas(wb, config)` and
  `apply_conditional_formatting(wb, config)`
- The Oracle Severity lookup formula (col R), the Total Risk Score formula (col T),
  and the Risk Level IF formula (col U) are applied across all data rows
- The four conditional formatting rules on column U are applied
- Formula row range is driven by `config["max_rows"]`

**Todo List**
1. Move formula loop from `run.py` lines 446–472 into `apply_formulas(wb, config)`
2. Move conditional formatting rules from lines 478–508 into
   `apply_conditional_formatting(wb, config)` — import fill objects from `src/styles`
3. No separate test — covered by integration test

**Relevant Context**
- Source lines in `run.py`: 446–508
- FormulaRule imports from `openpyxl.formatting.rule`

**Status** — [x] done

---

### Sub-Task 8 — Create `src/charts.py`

**Intent**
Extract chart and Executive Summary population from `run.py` into its own module.

**Expected Outcomes**
- `src/charts.py` exposes `build_executive_summary(wb)`
- The dashboard title, client/release selector cells, COUNTIFS KPI formulas, and
  the Pie Chart are all built inside this function

**Todo List**
1. Move `exec_ws` population from `run.py` lines 514–563 into `build_executive_summary(wb)`
2. No separate test — covered by integration test

**Relevant Context**
- Source lines in `run.py`: 514–563

**Status** — [x] done

---

### Sub-Task 9 — Create `src/protection.py`

**Intent**
Extract workbook sheet protection and formula-cell locking from `run.py` into a dedicated
module, consistent with the one-concern-per-module pattern.

**Expected Outcomes**
- `src/protection.py` exposes `apply_protection(wb, config)`
- Protected tabs (`Scoring_Rules`, `Reference_Lists`, `Metadata_Config`, `Data_Lineage`,
  `PowerQuery_Control`) have `sheet.protection.sheet = True`
- Formula columns (R, T, U) in `Impact_Assessments` rows 2–`max_rows` have
  `cell.protection = Protection(locked=True)`

**Todo List**
1. Move protected-tab loop from `run.py` lines 839–848
2. Move formula-cell locking loop from `run.py` lines 854–863
3. Wrap in `apply_protection(wb, config)`

**Relevant Context**
- Source lines in `run.py`: 839–863
- `Protection` is already imported from `openpyxl.styles` in `run.py`

**Status** — [x] done

---

### Sub-Task 10 — Create `src/main.py` and integration test

**Intent**
Wire all modules together into a clean entrypoint. `main.py` is the only place where
modules are orchestrated; it calls each builder function in order and saves the workbook.

**Expected Outcomes**
- `src/main.py` calls: `load_config` → `init_styles` → `build_workbook` →
  `populate_reference_lists` → `apply_validations` → `apply_formulas` →
  `apply_conditional_formatting` → `build_executive_summary` → `apply_protection` → `wb.save()`
- Running `python src/main.py` from the project root produces
  `output/Oracle_Fusion_Impact_Analyzer_Enterprise.xlsx`
- The output path is resolved from `config["output_file"]`
- `tests/test_integration.py` calls `main.generate()` (extracted helper) and asserts the
  output file exists and contains the expected sheet names
- `run.py` is **deleted** after the integration test passes

**Todo List**
1. Write `src/main.py` with a `generate(config_path=None)` function and an
   `if __name__ == "__main__"` guard
2. Ensure the output is written to `output/` subdirectory (create if missing)
3. Write `tests/test_integration.py` — call `generate()`, assert file exists,
   open with openpyxl, check sheet count >= 40
4. Delete `run.py` after the integration test passes

**Relevant Context**
- Call order matters: reference lists must exist before validations; styles must be
  initialised before `build_workbook`; `apply_protection` must be called last before save
- `src/protection.py` created in Sub-Task 9

**Status** — [x] done

---

## Non-Goals

- No change to the generated workbook content or structure
- No Oracle DB connectivity (separate future task)
- No AI feature implementation (separate future task)
- No CI/CD pipeline setup
