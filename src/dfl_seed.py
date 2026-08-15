"""
dfl_seed.py
-----------
Dignity Funerals Limited (DFL) — Oracle Fusion 26C Impact Assessment seed data.

Populates the Oracle Fusion Impact Analyzer workbook with DFL-specific data:
  - Client registration for DFL
  - Oracle 26C release record
  - In-scope release changes (ERP Financials, HCM Payroll/HR/Absence/Time, SCM Inventory)
  - DFL business processes
  - DFL applications and configurations
  - Impact assessments with calculated risk scores

Usage
-----
    from src.dfl_seed import seed_dfl
    seed_dfl(wb)            # populates DFL data into an already-built workbook
"""

from __future__ import annotations

from datetime import date

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

_CLIENT_ID   = "CLT_DFL001"
_RELEASE_ID  = "REL_26C"
_TODAY       = date.today().isoformat()

# In-scope change IDs for DFL
# Format: CHG_<MODULE>_<NNN>
_CHANGES: list[dict] = [

    # ── HCM / PAYROLL (Critical for DFL — 4,000+ employees across UK funeral homes) ──
    {
        "id": "CHG_PAY_001",
        "title": "Payroll Element Eligibility — Enhanced Period-Specific Rules",
        "description": (
            "New period-specific eligibility rules for payroll elements allow more granular "
            "control over which employees receive specific payroll components (e.g. night shift "
            "uplift, on-call allowances). DFL must review existing element eligibility configurations "
            "to ensure funeral director on-call and weekend allowances still apply correctly."
        ),
        "module": "Payroll",
        "feature_area": "Element Processing",
        "change_type": "Functional",
        "tech_object": "PAY_ELEMENT_ELIGIBILITY",
        "api_service": "",
        "config_area": "Payroll Configuration",
        "security_flag": "N",
        "compliance_flag": "Y",
        "deprecation_flag": "N",
        "required_action": "Review and validate on-call/shift element eligibility rules in UAT",
        "severity": "High",
        "section": "Payroll 26C What's New",
    },
    {
        "id": "CHG_PAY_002",
        "title": "Payroll Run Results — Archive Enhancement for Legislative Changes",
        "description": (
            "Enhanced payroll run result archiving to support UK legislative changes including "
            "2025 NI thresholds and minimum wage uplifts. Auto-enabled — requires validation that "
            "DFL payroll results reconcile correctly after upgrade to 26C."
        ),
        "module": "Payroll",
        "feature_area": "Payroll Processing",
        "change_type": "Legislative",
        "tech_object": "PAY_RUN_RESULTS",
        "api_service": "",
        "config_area": "UK Payroll",
        "security_flag": "N",
        "compliance_flag": "Y",
        "deprecation_flag": "N",
        "required_action": "Run parallel payroll in UAT — validate NI/tax/minimum wage calculations match HMRC expectations",
        "severity": "Critical",
        "section": "Payroll 26C What's New",
    },
    {
        "id": "CHG_PAY_003",
        "title": "P60 / P45 End-of-Year Report Redwood Migration",
        "description": (
            "End-of-year statutory reports (P60, P45) migrated to Redwood UI. DFL HR administrators "
            "will see a new interface for generating and distributing year-end statutory documents. "
            "Employee self-service access to P60s is unchanged."
        ),
        "module": "Payroll",
        "feature_area": "Statutory Reporting",
        "change_type": "UI",
        "tech_object": "UK_EOY_REPORTS",
        "api_service": "",
        "config_area": "UK Statutory",
        "security_flag": "N",
        "compliance_flag": "Y",
        "deprecation_flag": "N",
        "required_action": "Train payroll team on new Redwood P60/P45 screens",
        "severity": "Medium",
        "section": "Payroll 26C What's New",
    },

    # ── HCM / HUMAN RESOURCES ──
    {
        "id": "CHG_HR_001",
        "title": "Global HR — Person REST API v2 Breaking Change",
        "description": (
            "The /hcmRestApi/resources/11.13.18.05/workers endpoint introduces a new required "
            "field 'legalEmployerName' in the response schema. DFL's HR integration with the "
            "group HR reporting system must be updated to handle this field."
        ),
        "module": "Human Resources",
        "feature_area": "REST APIs",
        "change_type": "Technical",
        "tech_object": "",
        "api_service": "HCM REST /workers v2",
        "config_area": "",
        "security_flag": "N",
        "compliance_flag": "N",
        "deprecation_flag": "N",
        "required_action": "Update HR integration consumer code to handle new 'legalEmployerName' field",
        "severity": "High",
        "section": "Human Resources 26C What's New",
    },
    {
        "id": "CHG_HR_002",
        "title": "Employment Contract Type — New Field for Zero-Hours Contracts",
        "description": (
            "New 'ZeroHoursIndicator' field added to Employment Contracts to support UK employment law "
            "compliance for zero-hours contract workers. DFL employs casual funeral assistants on "
            "zero-hours contracts and must configure this field and update HR data for compliance."
        ),
        "module": "Human Resources",
        "feature_area": "Employment Contracts",
        "change_type": "Functional",
        "tech_object": "PER_EMPLOYMENT_CONTRACT",
        "api_service": "",
        "config_area": "UK Employment",
        "security_flag": "N",
        "compliance_flag": "Y",
        "deprecation_flag": "N",
        "required_action": "Configure ZeroHoursIndicator — update data for ~320 casual employees",
        "severity": "High",
        "section": "Human Resources 26C What's New",
    },
    {
        "id": "CHG_HR_003",
        "title": "Redwood People Management — Manager Self-Service Migration",
        "description": (
            "Manager self-service pages for viewing team, managing direct reports, and approving "
            "HR transactions migrated to Redwood UX. DFL's 400+ branch managers will see a "
            "redesigned interface. Training and comms required."
        ),
        "module": "Human Resources",
        "feature_area": "Manager Self-Service",
        "change_type": "UI",
        "tech_object": "",
        "api_service": "",
        "config_area": "HCM Personalisation",
        "security_flag": "N",
        "compliance_flag": "N",
        "deprecation_flag": "N",
        "required_action": "Update manager training materials; communicate UI change to branch managers",
        "severity": "Medium",
        "section": "Human Resources 26C What's New",
    },

    # ── HCM / ABSENCE MANAGEMENT ──
    {
        "id": "CHG_ABS_001",
        "title": "Absence Plan Accrual — Enhanced Carry Forward Limits",
        "description": (
            "New configuration options for absence plan carry-forward limits with "
            "automatic expiry rules. DFL's annual leave plans (25 days standard, 28 days "
            "for senior staff) may need configuration review to ensure carry-forward "
            "rules remain compliant with DFL policy."
        ),
        "module": "Absence Management",
        "feature_area": "Absence Plans",
        "change_type": "Functional",
        "tech_object": "ANC_PLAN_ACCRUALS",
        "api_service": "",
        "config_area": "Absence Configuration",
        "security_flag": "N",
        "compliance_flag": "Y",
        "deprecation_flag": "N",
        "required_action": "Review DFL annual leave carry-forward configuration for 26C compatibility",
        "severity": "Medium",
        "section": "Absence Management 26C What's New",
    },
    {
        "id": "CHG_ABS_002",
        "title": "Bereavement Leave — New Statutory Type Support",
        "description": (
            "New absence type template for statutory bereavement leave (Parental Bereavement "
            "Leave, extended bereavement). Given DFL's nature as a bereavement services "
            "company, correct configuration is essential. Oracle adds support for "
            "'Day One Right' bereavement leave types."
        ),
        "module": "Absence Management",
        "feature_area": "Absence Types",
        "change_type": "Functional",
        "tech_object": "ANC_ABSENCE_TYPES",
        "api_service": "",
        "config_area": "Absence Configuration",
        "security_flag": "N",
        "compliance_flag": "Y",
        "deprecation_flag": "N",
        "required_action": "Configure new statutory bereavement leave types; review DFL bereavement policy alignment",
        "severity": "High",
        "section": "Absence Management 26C What's New",
    },

    # ── HCM / TIME AND LABOR ──
    {
        "id": "CHG_TL_001",
        "title": "Time Card — Shift Differential Auto-Calculation Enhancement",
        "description": (
            "Enhanced shift differential auto-calculation for multi-day time cards, "
            "including overnight funeral director duty shifts. DFL's time recording for "
            "24/7 on-call funeral directors benefits from this change but requires "
            "configuration validation."
        ),
        "module": "Time and Labor",
        "feature_area": "Time Card Processing",
        "change_type": "Functional",
        "tech_object": "OTL_TIMECARD",
        "api_service": "",
        "config_area": "Time & Labor Config",
        "security_flag": "N",
        "compliance_flag": "N",
        "deprecation_flag": "N",
        "required_action": "Validate shift differential calculations for on-call funeral directors in UAT",
        "severity": "Medium",
        "section": "Time and Labor 26C What's New",
    },

    # ── HCM / WORKFORCE SCHEDULING ──
    {
        "id": "CHG_WFS_001",
        "title": "Workforce Scheduling — On-Call Rota AI Suggestions",
        "description": (
            "New AI-assisted on-call rota scheduling suggests optimal coverage based on "
            "historical demand patterns. For DFL this could optimise funeral director "
            "on-call rotas across 500 branches. Feature requires opt-in configuration."
        ),
        "module": "Workforce Scheduling",
        "feature_area": "Rota Management",
        "change_type": "AI Feature",
        "tech_object": "",
        "api_service": "",
        "config_area": "Scheduling Configuration",
        "security_flag": "N",
        "compliance_flag": "N",
        "deprecation_flag": "N",
        "required_action": "Evaluate AI rota suggestions feature for DFL operational use; configure if beneficial",
        "severity": "Low",
        "section": "Workforce Scheduling 26C What's New",
    },

    # ── ERP / FINANCIALS ──
    {
        "id": "CHG_FIN_001",
        "title": "Accounts Payable — Invoice AI Matching Enhancement",
        "description": (
            "AI-powered invoice-to-PO matching now supports multi-line partial PO matching "
            "for service-based invoices. DFL processes high volumes of supplier invoices "
            "for funeral supplies (caskets, flowers, embalming materials). This will "
            "improve match rates for split deliveries."
        ),
        "module": "Financials",
        "feature_area": "Accounts Payable",
        "change_type": "AI Feature",
        "tech_object": "AP_INVOICES",
        "api_service": "",
        "config_area": "AP Matching",
        "security_flag": "N",
        "compliance_flag": "N",
        "deprecation_flag": "N",
        "required_action": "Configure AI matching tolerance for DFL supplier invoice patterns; test against top 20 suppliers",
        "severity": "Medium",
        "section": "Financials 26C What's New",
    },
    {
        "id": "CHG_FIN_002",
        "title": "General Ledger — Period Close Redwood UI Migration",
        "description": (
            "Month-end and period close tasks migrated to Redwood interface. DFL's finance "
            "team (centralised at Sutton Coldfield HQ) will encounter a new period close "
            "checklist interface. Monthly close processes across 500 trading entities "
            "should be tested end-to-end."
        ),
        "module": "Financials",
        "feature_area": "General Ledger",
        "change_type": "UI",
        "tech_object": "GL_PERIOD_CLOSE",
        "api_service": "",
        "config_area": "GL Configuration",
        "security_flag": "N",
        "compliance_flag": "N",
        "deprecation_flag": "N",
        "required_action": "Train finance team on new Redwood period close UI; run month-end simulation in UAT",
        "severity": "High",
        "section": "Financials 26C What's New",
    },
    {
        "id": "CHG_FIN_003",
        "title": "Fixed Assets — Depreciation Schedule API Deprecation",
        "description": (
            "The legacy SOAP-based Fixed Assets depreciation schedule API "
            "(/FinancialCommonErpIntegration/FixedAssets) is deprecated in 26C and will "
            "be removed in 27A. DFL's asset register integration must migrate to the "
            "REST API equivalent."
        ),
        "module": "Financials",
        "feature_area": "Fixed Assets",
        "change_type": "Technical",
        "tech_object": "FA_DEPRECIATION_API",
        "api_service": "FixedAssets SOAP → REST migration",
        "config_area": "",
        "security_flag": "N",
        "compliance_flag": "N",
        "deprecation_flag": "Y",
        "required_action": "URGENT: Migrate Fixed Assets SOAP integration to REST before 27A (target: 26C UAT)",
        "severity": "Critical",
        "section": "Financials 26C What's New",
    },
    {
        "id": "CHG_FIN_004",
        "title": "Revenue Management — Performance Obligation Identification Enhancement",
        "description": (
            "Enhanced rules engine for IFRS 15 / ASC 606 performance obligation identification. "
            "DFL's funeral package revenue recognition (bundled at-need and pre-need funeral "
            "plans) may be impacted by new identification logic. Finance team review required."
        ),
        "module": "Financials",
        "feature_area": "Revenue Management",
        "change_type": "Functional",
        "tech_object": "ORA_REVENUE_MGMT",
        "api_service": "",
        "config_area": "Revenue Configuration",
        "security_flag": "N",
        "compliance_flag": "Y",
        "deprecation_flag": "N",
        "required_action": "Review funeral package revenue recognition templates for IFRS 15 compliance under new rules",
        "severity": "High",
        "section": "Financials 26C What's New",
    },
    {
        "id": "CHG_FIN_005",
        "title": "Accounts Receivable — Pre-need Funeral Plan Deferred Revenue Tracking",
        "description": (
            "New deferred revenue tracking capability for long-term advance payment contracts. "
            "Highly relevant for DFL's pre-need funeral plans (e.g. Golden Charter, Dignity "
            "Plans) where funds are held in trust. New reporting visibility improves statutory "
            "compliance."
        ),
        "module": "Financials",
        "feature_area": "Accounts Receivable",
        "change_type": "Functional",
        "tech_object": "AR_DEFERRED_REVENUE",
        "api_service": "",
        "config_area": "AR Configuration",
        "security_flag": "N",
        "compliance_flag": "Y",
        "deprecation_flag": "N",
        "required_action": "Configure deferred revenue tracking for DFL pre-need plans; align with trust accounting",
        "severity": "Medium",
        "section": "Financials 26C What's New",
    },

    # ── ERP / PROCUREMENT ──
    {
        "id": "CHG_PRC_001",
        "title": "Purchasing — Supplier Portal Redwood Migration",
        "description": (
            "Supplier portal fully migrated to Redwood UX. DFL's ~2,000 active suppliers "
            "(coffin manufacturers, florists, embalming suppliers, crematoria) will "
            "experience a new portal interface. Supplier onboarding and invoice submission "
            "workflows must be tested."
        ),
        "module": "Procurement",
        "feature_area": "Supplier Management",
        "change_type": "UI",
        "tech_object": "PO_SUPPLIER_PORTAL",
        "api_service": "",
        "config_area": "Procurement Configuration",
        "security_flag": "N",
        "compliance_flag": "N",
        "deprecation_flag": "N",
        "required_action": "Communicate Redwood portal change to key suppliers; update supplier onboarding guides",
        "severity": "Medium",
        "section": "Procurement 26C What's New",
    },
    {
        "id": "CHG_PRC_002",
        "title": "Contract Management — AI Contract Analysis (Opt-In)",
        "description": (
            "New AI-powered contract analysis feature identifies risk clauses and obligation "
            "summaries for procurement contracts. Opt-in feature requiring configuration. "
            "DFL's legal and procurement teams manage 500+ supplier contracts; AI analysis "
            "could accelerate contract reviews."
        ),
        "module": "Procurement",
        "feature_area": "Contract Management",
        "change_type": "AI Feature",
        "tech_object": "",
        "api_service": "",
        "config_area": "Contract Config",
        "security_flag": "N",
        "compliance_flag": "N",
        "deprecation_flag": "N",
        "required_action": "Evaluate AI contract analysis for DFL; seek legal and IT security sign-off before enabling",
        "severity": "Low",
        "section": "Procurement 26C What's New",
    },

    # ── ERP / PROJECT MANAGEMENT ──
    {
        "id": "CHG_PM_001",
        "title": "Project Costing — Funeral Branch Renovation Project Templates",
        "description": (
            "Enhanced project template capabilities supporting multi-phase capital projects. "
            "DFL's ongoing branch refurbishment programme (50+ branches p.a.) uses Oracle "
            "Project Management to track renovation costs. New template enhancements streamline "
            "project setup."
        ),
        "module": "Project Management",
        "feature_area": "Project Costing",
        "change_type": "Functional",
        "tech_object": "PJC_PROJECTS",
        "api_service": "",
        "config_area": "Project Config",
        "security_flag": "N",
        "compliance_flag": "N",
        "deprecation_flag": "N",
        "required_action": "Review project template configurations for branch refurbishment programme",
        "severity": "Low",
        "section": "Project Management 26C What's New",
    },

    # ── SCM / INVENTORY MANAGEMENT ──
    {
        "id": "CHG_INV_001",
        "title": "Inventory Management — Lot/Serial Number Tracking Enhancement",
        "description": (
            "Enhanced lot and serial number tracking for regulated inventory items. "
            "DFL tracks certain embalming chemicals and medical-grade supplies by lot number "
            "for regulatory compliance. Improved tracking reduces reconciliation effort."
        ),
        "module": "Inventory Management",
        "feature_area": "Inventory Tracking",
        "change_type": "Functional",
        "tech_object": "INV_LOT_TRACKING",
        "api_service": "",
        "config_area": "Inventory Configuration",
        "security_flag": "N",
        "compliance_flag": "Y",
        "deprecation_flag": "N",
        "required_action": "Configure lot tracking for regulated embalming supplies; validate COSHH compliance data",
        "severity": "Medium",
        "section": "Inventory Management 26C What's New",
    },
    {
        "id": "CHG_INV_002",
        "title": "Inventory Replenishment — AI Demand Forecasting",
        "description": (
            "New AI demand forecasting for inventory replenishment planning. For DFL, "
            "this could predict seasonal demand for funeral supplies (higher winter demand). "
            "Opt-in feature requiring ML model training on DFL historical data."
        ),
        "module": "Inventory Management",
        "feature_area": "Replenishment",
        "change_type": "AI Feature",
        "tech_object": "",
        "api_service": "",
        "config_area": "Inventory Config",
        "security_flag": "N",
        "compliance_flag": "N",
        "deprecation_flag": "N",
        "required_action": "Evaluate AI demand forecasting; assess data quality requirements before enabling",
        "severity": "Low",
        "section": "Inventory Management 26C What's New",
    },

    # ── SCM / ORDER MANAGEMENT ──
    {
        "id": "CHG_OM_001",
        "title": "Order Management — Service Order REST API Enhancement",
        "description": (
            "New fields added to the Sales Order REST API for service-type orders, "
            "including service delivery date scheduling and location attributes. "
            "DFL's funeral case management integration uses Order Management for "
            "at-need funeral service orders; API changes need testing."
        ),
        "module": "Order Management",
        "feature_area": "Service Orders",
        "change_type": "Technical",
        "tech_object": "",
        "api_service": "OM REST /salesOrders",
        "config_area": "",
        "security_flag": "N",
        "compliance_flag": "N",
        "deprecation_flag": "N",
        "required_action": "Test funeral case management system integration against updated OM REST API schema",
        "severity": "High",
        "section": "Order Management 26C What's New",
    },

    # ── HCM / RECRUITING ──
    {
        "id": "CHG_RCT_001",
        "title": "Recruiting — AI-Assisted Job Description Optimisation",
        "description": (
            "AI-powered job description analysis suggests improvements for diversity "
            "and candidate attraction. DFL recruits ~800 funeral directors and support "
            "staff annually. AI suggestions on job descriptions could improve "
            "candidate quality and diversity metrics."
        ),
        "module": "Recruiting",
        "feature_area": "Job Requisitions",
        "change_type": "AI Feature",
        "tech_object": "",
        "api_service": "",
        "config_area": "Recruiting Config",
        "security_flag": "N",
        "compliance_flag": "N",
        "deprecation_flag": "N",
        "required_action": "Enable AI job description optimisation; brief HR team on capabilities and limitations",
        "severity": "Low",
        "section": "Recruiting 26C What's New",
    },

    # ── HCM / COMPENSATION ──
    {
        "id": "CHG_CMP_001",
        "title": "Compensation — Salary Range AI Recommendations",
        "description": (
            "New AI-powered salary range recommendations integrated with Oracle Fusion "
            "Compensation benchmarking data. Requires opt-in. DFL can use this to "
            "benchmark funeral director and support staff salaries against market data."
        ),
        "module": "Compensation",
        "feature_area": "Salary Management",
        "change_type": "AI Feature",
        "tech_object": "",
        "api_service": "",
        "config_area": "Compensation Config",
        "security_flag": "N",
        "compliance_flag": "N",
        "deprecation_flag": "N",
        "required_action": "Review AI salary benchmarking capability; assess data governance requirements",
        "severity": "Low",
        "section": "Compensation 26C What's New",
    },

    # ── HCM / BENEFITS ──
    {
        "id": "CHG_BEN_001",
        "title": "Benefits — Enhanced Life Events Auto-Processing",
        "description": (
            "Automated life event processing now handles 12 additional qualifying life "
            "events with configurable enrolment windows. DFL's benefits (life assurance, "
            "BUPA, pension top-up) need life event rules reviewed to ensure new event "
            "types trigger correct benefit changes."
        ),
        "module": "Benefits",
        "feature_area": "Life Events",
        "change_type": "Functional",
        "tech_object": "BEN_LIFE_EVENTS",
        "api_service": "",
        "config_area": "Benefits Configuration",
        "security_flag": "N",
        "compliance_flag": "Y",
        "deprecation_flag": "N",
        "required_action": "Review life event rules for DFL benefit plans; test auto-processing of new event types",
        "severity": "Medium",
        "section": "Benefits 26C What's New",
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _write_rows(ws, rows: list[list]) -> None:
    for r_idx, row in enumerate(rows, start=2):
        for c_idx, val in enumerate(row, start=1):
            ws.cell(row=r_idx, column=c_idx, value=val)


# ──────────────────────────────────────────────────────────────────────────────
# Sheet seeders
# ──────────────────────────────────────────────────────────────────────────────

def _seed_dfl_client(wb) -> None:
    _write_rows(wb["Clients"], [
        [
            _CLIENT_ID,
            "Dignity Funerals Limited",
            "DFL",
            "Funeral Services",
            "UK",
            "Group IT Director",
            "Managed Service",
            "High",
            "Active",
        ],
    ])


def _seed_dfl_release(wb) -> None:
    _write_rows(wb["Oracle_Releases"], [
        [
            _RELEASE_ID,
            "Oracle Fusion 26C",
            2025,
            "Q2",
            "ERP/HCM/SCM",
            "2025-06-20",
            "https://docs.oracle.com/en/cloud/saas/readiness/erp/26c/",
            _TODAY,
            "Active",
        ],
    ])


def _seed_dfl_changes(wb) -> None:
    ws = wb["Release_Changes"]
    for r_offset, chg in enumerate(_CHANGES):
        row = [
            chg["id"],
            _RELEASE_ID,
            chg["title"],
            chg["description"],
            chg["module"],
            chg["feature_area"],
            chg["change_type"],
            chg.get("tech_object", ""),
            chg.get("api_service", ""),
            chg.get("config_area", ""),
            chg.get("security_flag", "N"),
            chg.get("compliance_flag", "N"),
            chg.get("deprecation_flag", "N"),
            chg.get("required_action", ""),
            chg["severity"],
            "2025-06-20",
            f"Oracle Fusion 26C Readiness — {chg['module']}",
            chg.get("section", ""),
        ]
        for c_idx, val in enumerate(row, start=1):
            ws.cell(row=r_offset + 2, column=c_idx, value=val)


def _seed_dfl_business_processes(wb) -> None:
    _write_rows(wb["Business_Processes"], [
        ["BP_DFL_001", "Payroll Processing",        "Payroll",          "UK Monthly Payroll",         "Payroll Manager",       "Critical", "Active"],
        ["BP_DFL_002", "Hire to Retire",            "Human Resources",  "HR Onboarding/Offboarding",  "HR Director",           "Critical", "Active"],
        ["BP_DFL_003", "Absence & Leave",           "Absence Mgmt",     "Annual Leave / Sickness",    "HR Manager",            "High",     "Active"],
        ["BP_DFL_004", "Time Recording",            "Time and Labor",   "On-call / Shift Recording",  "Ops Manager",           "High",     "Active"],
        ["BP_DFL_005", "Procure to Pay",            "Financials",       "Supplier Invoice Processing","AP Manager",            "Critical", "Active"],
        ["BP_DFL_006", "Revenue Recognition",       "Financials",       "Pre-need / At-need Revenue", "Finance Controller",    "Critical", "Active"],
        ["BP_DFL_007", "Period Close",              "Financials",       "Month End Close",            "Financial Controller",  "Critical", "Active"],
        ["BP_DFL_008", "Supplier Management",       "Procurement",      "Supplier Onboarding & PO",   "Procurement Manager",   "High",     "Active"],
        ["BP_DFL_009", "Funeral Supply Chain",      "Inventory Mgmt",   "Casket/Supply Inventory",    "Supply Chain Manager",  "High",     "Active"],
        ["BP_DFL_010", "Funeral Case Management",   "Order Management", "At-need Service Orders",     "Operations Director",   "Critical", "Active"],
        ["BP_DFL_011", "Workforce Scheduling",      "Workforce Sched",  "Branch Rota & On-call",      "Regional Manager",      "High",     "Active"],
        ["BP_DFL_012", "Talent Acquisition",        "Recruiting",       "Funeral Director Recruitment","HR Talent Lead",       "Medium",   "Active"],
        ["BP_DFL_013", "Branch Capex Projects",     "Project Mgmt",     "Branch Refurbishment",       "Estates Manager",       "Medium",   "Active"],
    ])


def _seed_dfl_applications(wb) -> None:
    _write_rows(wb["Applications"], [
        ["APP_DFL_001", "Oracle Fusion ERP",          "SaaS",        "Oracle",        "26C",  "PROD", "Critical", "Active"],
        ["APP_DFL_002", "Oracle Fusion HCM",          "SaaS",        "Oracle",        "26C",  "PROD", "Critical", "Active"],
        ["APP_DFL_003", "Oracle Fusion SCM",          "SaaS",        "Oracle",        "26C",  "PROD", "High",     "Active"],
        ["APP_DFL_004", "DFL Case Mgmt System",       "On-Premise",  "Internal",      "v4.2", "PROD", "Critical", "Active"],
        ["APP_DFL_005", "DFL Branch POS",             "On-Premise",  "Tillpoint",     "v2.1", "PROD", "High",     "Active"],
        ["APP_DFL_006", "Dignity Pre-need Portal",    "SaaS",        "Third Party",   "v3.0", "PROD", "High",     "Active"],
        ["APP_DFL_007", "HR Reporting (BI)",          "SaaS",        "Oracle OTBI",   "26C",  "PROD", "Medium",   "Active"],
        ["APP_DFL_008", "Sage Payroll (legacy)",      "On-Premise",  "Sage",          "2023", "PROD", "Low",      "Decommission"],
    ])


def _seed_dfl_environments(wb) -> None:
    _write_rows(wb["Environments"], [
        ["ENV_DFL_001", "Production",  "PROD", "Oracle",    "Oracle Cloud", "Critical", "Active",  "2025-06-20"],
        ["ENV_DFL_002", "UAT",         "UAT",  "Oracle",    "Oracle Cloud", "High",     "Active",  "2025-05-20"],
        ["ENV_DFL_003", "Dev/Sandbox", "DEV",  "Oracle",    "Oracle Cloud", "Medium",   "Active",  "2025-04-20"],
    ])


def _seed_dfl_configurations(wb) -> None:
    _write_rows(wb["Configurations"], [
        ["CFG_DFL_001", "UK Payroll Elements",       "Payroll",    "On-call allowance, shift uplift, night differential", "Payroll Team",    "Critical", "Active"],
        ["CFG_DFL_002", "Absence Plans",             "Absence",    "25/28 day annual leave, carry-forward rules",          "HR Team",         "High",     "Active"],
        ["CFG_DFL_003", "Employment Contract Types", "HR",         "Permanent, Fixed-term, Zero-hours contractor",         "HR Team",         "High",     "Active"],
        ["CFG_DFL_004", "AP Invoice Matching",       "Financials", "PO-based 3-way match, tolerance rules",                "AP Team",         "High",     "Active"],
        ["CFG_DFL_005", "Revenue Recognition Rules", "Financials", "Pre-need deferred, at-need immediate",                 "Finance",         "Critical", "Active"],
        ["CFG_DFL_006", "Supplier Portal",           "Procurement","Approved supplier list, EDI invoicing",                "Procurement",     "High",     "Active"],
        ["CFG_DFL_007", "Inventory Lot Tracking",    "SCM",        "Embalming chemicals, medical consumables",             "Supply Chain",    "Medium",   "Active"],
        ["CFG_DFL_008", "Branch Rota Rules",         "Scheduling", "On-call rota patterns, emergency cover rules",         "Operations",      "High",     "Active"],
        ["CFG_DFL_009", "Fixed Assets Register",     "Financials", "Funeral homes, vehicles, equipment",                   "Finance",         "High",     "Active"],
        ["CFG_DFL_010", "Benefit Plans",             "Benefits",   "BUPA, life assurance, pension, DIS",                   "HR Benefits",     "High",     "Active"],
    ])


def _seed_dfl_impact_assessments(wb) -> None:
    """Generate impact assessments for each DFL change."""
    # Severity → Oracle score
    sev_score = {"Critical": 5, "High": 4, "Medium": 3, "Low": 1}
    # Module → business criticality score for DFL
    module_biz = {
        "Payroll":              5,
        "Human Resources":      5,
        "Absence Management":   4,
        "Time and Labor":       4,
        "Financials":           5,
        "Procurement":          4,
        "Benefits":             4,
        "Compensation":         3,
        "Recruiting":           3,
        "Learning and Development": 2,
        "Workforce Scheduling": 4,
        "Project Management":   2,
        "Inventory Management": 3,
        "Order Management":     4,
        "Risk Management":      2,
        "HCM Common":           1,
        "Common Technologies and User Experience": 1,
        "Oracle Me Employee Experience": 1,
        "Talent Management":    2,
        "Self Service Financials": 2,
        "Self Service Procurement": 3,
        "Dynamic Skills":       1,
        "Opportunity Marketplace": 1,
        "Work Life":            1,
    }
    # change_type → custom score
    change_type_custom = {
        "Technical":    5,
        "Legislative":  4,
        "Functional":   3,
        "UI":           2,
        "AI Feature":   1,
    }
    # Pillars for each module (for integration score)
    module_integration = {
        "Payroll":              3,
        "Human Resources":      3,
        "Absence Management":   2,
        "Time and Labor":       2,
        "Financials":           5,
        "Procurement":          4,
        "Benefits":             2,
        "Compensation":         2,
        "Recruiting":           2,
        "Learning and Development": 1,
        "Workforce Scheduling": 2,
        "Project Management":   2,
        "Inventory Management": 3,
        "Order Management":     4,
        "Risk Management":      1,
        "HCM Common":           1,
        "Common Technologies and User Experience": 2,
        "Oracle Me Employee Experience": 1,
        "Talent Management":    2,
        "Self Service Financials": 2,
        "Self Service Procurement": 2,
        "Dynamic Skills":       1,
        "Opportunity Marketplace": 1,
        "Work Life":            1,
    }

    ws = wb["Impact_Assessments"]
    for r_offset, chg in enumerate(_CHANGES):
        asmt_id  = f"ASMT_{r_offset + 1:03d}"
        mod      = chg["module"]
        biz_crit = module_biz.get(mod, 2)
        custom   = change_type_custom.get(chg["change_type"], 2)
        integ    = module_integration.get(mod, 2)
        sec      = 3 if chg.get("security_flag") == "Y" else 1
        env      = 3  # all DFL changes touch PROD
        is_dep   = chg.get("deprecation_flag") == "Y"
        has_api  = bool(chg.get("api_service"))
        direct   = "Y"
        is_dep_flag = "Y" if is_dep else "N"
        is_cust  = "Y" if custom >= 4 else "N"
        is_api   = "Y" if has_api else "N"
        oracle_sev = sev_score.get(chg["severity"], 2)

        row = [
            asmt_id,
            _CLIENT_ID,
            _RELEASE_ID,
            chg["id"],
            chg["change_type"],
            "Configuration" if not has_api else "Interface",
            f"CFG_DFL_{(r_offset % 10) + 1:03d}" if not has_api else "",
            f"DFL {chg['module']} impacted by {chg['change_type'].lower()} change",
            direct,
            "N",
            is_cust,
            "N" if chg.get("security_flag") == "N" else "Y",
            biz_crit,
            custom,
            integ,
            sec,
            env,
            None,        # R — formula: Oracle severity score
            oracle_sev,  # S — history score (using oracle score as proxy)
            None,        # T — Total (formula)
            None,        # U — Risk Level (formula)
            "Pending Review",
            "",
            "",
            chg["required_action"],
            "Y" if chg["severity"] in ("Critical", "High", "Medium") else "N",
            "Y" if chg["severity"] in ("Critical", "High") else "N",
        ]
        for c_idx, val in enumerate(row, start=1):
            if c_idx in (18, 20, 21):  # formula cells
                continue
            ws.cell(row=r_offset + 2, column=c_idx, value=val)


def _seed_dfl_remediation(wb) -> None:
    # Only the Critical/High items get remediation actions
    high_changes = [c for c in _CHANGES if c["severity"] in ("Critical", "High")]
    rows = []
    for i, chg in enumerate(high_changes):
        rows.append([
            f"REM_DFL_{i + 1:03d}",
            f"ASMT_{_CHANGES.index(chg) + 1:03d}" if chg in _CHANGES else "",
            _CLIENT_ID,
            _RELEASE_ID,
            chg["required_action"][:100],
            "Team Lead",
            "2025-08-15",
            "Not Started",
            "High" if chg["severity"] == "Critical" else "Medium",
            "",
            "2025-09-01",
        ])
    _write_rows(wb["Remediation_Actions"], rows)


def _seed_dfl_test_cases(wb) -> None:
    rows = []
    for i, chg in enumerate(_CHANGES):
        if chg["severity"] not in ("Critical", "High", "Medium"):
            continue
        rows.append([
            f"TC_DFL_{i + 1:03d}",
            f"ASMT_{i + 1:03d}",
            _CLIENT_ID,
            _RELEASE_ID,
            f"Validate: {chg['title'][:80]}",
            f"Test that DFL {chg['module']} behaves correctly after 26C upgrade",
            chg["module"],
            "Regression",
            "High" if chg["severity"] in ("Critical", "High") else "Medium",
            "Not Started",
            "UAT",
            "",
            "",
            "",
        ])
    _write_rows(wb["Test_Cases"], rows)


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────────

def seed_dfl(wb) -> None:
    """Seed all DFL 26C data into the workbook."""
    _seed_dfl_client(wb)
    _seed_dfl_release(wb)
    _seed_dfl_changes(wb)
    _seed_dfl_business_processes(wb)
    _seed_dfl_applications(wb)
    _seed_dfl_environments(wb)
    _seed_dfl_configurations(wb)
    _seed_dfl_impact_assessments(wb)
    _seed_dfl_remediation(wb)
    _seed_dfl_test_cases(wb)
