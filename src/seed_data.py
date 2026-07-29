"""
seed_data.py
------------
Populates every sheet with realistic demo rows and seeds the
tblSeverityMap table on Scoring_Rules so the Impact_Assessments
risk-score formulas resolve correctly.

Call ``seed_all(wb)`` from main.py after the workbook skeleton is built
but before protection is applied.
"""

from __future__ import annotations

from datetime import date
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

# ---------------------------------------------------------------------------
# Shared reference values (used across multiple sheets)
# ---------------------------------------------------------------------------

_CLIENT_ID   = "CLT_DEMO01"
_RELEASE_ID  = "REL_24Q3"
_CHANGE_IDS  = ["CHG_001", "CHG_002", "CHG_003"]
_TODAY       = date.today().isoformat()
_ENV_PROD    = "PROD"
_ENV_UAT     = "UAT"
_ENV_DEV     = "DEV"

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _write_rows(ws, rows: list[list]) -> None:
    """Write a list-of-lists starting at row 2."""
    for r_idx, row in enumerate(rows, start=2):
        for c_idx, val in enumerate(row, start=1):
            ws.cell(row=r_idx, column=c_idx, value=val)


# ---------------------------------------------------------------------------
# Individual sheet seeders
# ---------------------------------------------------------------------------

def _seed_clients(wb):
    _write_rows(wb["Clients"], [
        [_CLIENT_ID, "Acme Corporation",    "ACME",  "Manufacturing", "EMEA", "Jane Smith",   "Managed Service", "High",   "Active"],
        ["CLT_DEMO02", "Beta Retail Ltd",   "BETA",  "Retail",        "APAC", "John Lee",     "Support Only",    "Medium", "Active"],
        ["CLT_DEMO03", "Gamma Health NHS",  "GAMMA", "Healthcare",    "UK",   "Sarah Jones",  "Managed Service", "Critical","Active"],
    ])


def _seed_oracle_releases(wb):
    _write_rows(wb["Oracle_Releases"], [
        [_RELEASE_ID, "Oracle Fusion 24C", 2024, "Q3", "ERP",
         "2024-09-20", "https://www.oracle.com/readiness", _TODAY, "Active"],
        ["REL_24Q4", "Oracle Fusion 24D", 2024, "Q4", "HCM",
         "2024-12-20", "https://www.oracle.com/readiness", _TODAY, "Active"],
        ["REL_25Q1", "Oracle Fusion 25A", 2025, "Q1", "SCM",
         "2025-03-21", "https://www.oracle.com/readiness", "", "Planned"],
    ])


def _seed_release_changes(wb):
    _write_rows(wb["Release_Changes"], [
        [_CHANGE_IDS[0], _RELEASE_ID, "AP Invoice Validation Enhancement",
         "New validation rules added to AP invoice matching.",
         "Payables", "Invoice Processing", "Functional",
         "AP_INVOICE_MATCH", "", "Invoice Matching",
         "N", "N", "N", "Review matching rules", "High",
         "2024-09-20", "Doc ID 2987654", "Section 3.2"],
        [_CHANGE_IDS[1], _RELEASE_ID, "HCM Global HR REST API Change",
         "Breaking change to /workers endpoint response schema.",
         "HCM", "Global HR", "Technical",
         "", "HCM REST /workers", "",
         "N", "N", "N", "Update API consumers", "Critical",
         "2024-09-20", "Doc ID 2987700", "Section 7.1"],
        [_CHANGE_IDS[2], _RELEASE_ID, "SCM Inventory Opt-In Feature",
         "New opt-in feature for real-time inventory tracking.",
         "SCM", "Inventory", "Opt-In",
         "", "", "Inventory Config",
         "N", "N", "N", "Evaluate for adoption", "Low",
         "2024-09-20", "Doc ID 2987810", "Section 12.4"],
    ])


def _seed_business_processes(wb):
    _write_rows(wb["Business_Processes"], [
        ["BP_001", "Procure to Pay",    "Payables",    "Invoice Matching", "AP Manager",  "Critical", "Active"],
        ["BP_002", "Hire to Retire",    "HCM",         "Onboarding",       "HR Director", "High",     "Active"],
        ["BP_003", "Order to Cash",     "Receivables", "Billing",          "AR Manager",  "High",     "Active"],
        ["BP_004", "Record to Report",  "GL",          "Period Close",     "Controller",  "Critical", "Active"],
        ["BP_005", "Plan to Inventory", "SCM",         "Demand Planning",  "SCM Manager", "Medium",   "Active"],
    ])


def _seed_applications(wb):
    _write_rows(wb["Applications"], [
        ["APP_001", "Oracle Fusion ERP", "SaaS",       "Oracle", "24C", _ENV_PROD, "Critical", "Active"],
        ["APP_002", "Oracle Fusion HCM", "SaaS",       "Oracle", "24C", _ENV_PROD, "Critical", "Active"],
        ["APP_003", "Workday Payroll",   "SaaS",       "Workday","2024.1",_ENV_PROD,"High",    "Active"],
        ["APP_004", "Legacy ERP",        "On-Premise", "SAP",    "ECC 6","",        "Medium",  "Decommission"],
    ])


def _seed_interfaces(wb):
    _write_rows(wb["Interfaces"], [
        ["INT_001", "ERP to Payroll",   "Oracle ERP", "Workday",     "Outbound", "REST",  "Daily",  "High",   "Active"],
        ["INT_002", "HCM to AD",        "Oracle HCM", "Active Dir",  "Outbound", "SCIM",  "Hourly", "High",   "Active"],
        ["INT_003", "Bank Statements",  "HSBC",       "Oracle ERP",  "Inbound",  "SFTP",  "Daily",  "Critical","Active"],
        ["INT_004", "Tax Engine",       "Oracle ERP", "Vertex",      "Bidirect", "SOAP",  "RT",     "Medium", "Active"],
    ])


def _seed_jobs_batches(wb):
    _write_rows(wb["Jobs_Batches"], [
        ["JOB_001", "AP Payment Run",        "Weekly Mon 02:00", "Payables",   "AP_BATCH",  "Critical", "2024-09-16", "Active"],
        ["JOB_002", "GL Period Close",       "Monthly EOM",      "GL",         "GL_CLOSE",  "Critical", "2024-08-31", "Active"],
        ["JOB_003", "HCM Payroll Interface", "Bi-weekly Fri",    "HCM",        "HCM_PAY",   "High",     "2024-09-13", "Active"],
        ["JOB_004", "Inventory Reorder",     "Daily 06:00",      "SCM",        "SCM_INV",   "Medium",   "2024-09-16", "Active"],
    ])


def _seed_environments(wb):
    _write_rows(wb["Environments"], [
        ["ENV_001", "Production",    _ENV_PROD, "Oracle Fusion", "https://prod.example.com",  "Quarterly", "IT Ops",    "Active"],
        ["ENV_002", "UAT",           _ENV_UAT,  "Oracle Fusion", "https://uat.example.com",   "Monthly",   "QA Lead",   "Active"],
        ["ENV_003", "Development",   _ENV_DEV,  "Oracle Fusion", "https://dev.example.com",   "On-demand", "Dev Lead",  "Active"],
        ["ENV_004", "DR",            "DR",      "Oracle Fusion", "https://dr.example.com",    "Quarterly", "IT Ops",    "Active"],
    ])


def _seed_configurations(wb):
    _write_rows(wb["Configurations"], [
        ["CFG_001", "Payables",  "Invoice Matching",   "2-Way Match Tolerance", "5%",   "2024-06-01", "AP Manager",  "Active"],
        ["CFG_002", "GL",        "Period Control",     "Period Close Grace Days","3",    "2024-01-01", "Controller",  "Active"],
        ["CFG_003", "HCM",       "Absence Management", "Max Carry Forward Days","10",   "2024-04-01", "HR Director", "Active"],
        ["CFG_004", "Payables",  "Payment Terms",      "Default Payment Terms", "Net30","2023-01-01", "AP Manager",  "Active"],
    ])


def _seed_customizations(wb):
    _write_rows(wb["Customizations"], [
        ["CUS_001", "Payables",  "Report",     "AP Ageing Report",        "Custom AP ageing by supplier",  "Low",    "Finance IT", "Active"],
        ["CUS_002", "HCM",       "Fast Formula","Bonus Eligibility Formula","Determines bonus eligibility",  "Medium", "HR IT",      "Active"],
        ["CUS_003", "GL",        "Workflow",   "Journal Approval WF",     "Extended approval routing",     "Medium", "Finance IT", "Active"],
        ["CUS_004", "SCM",       "Extension",  "Inventory Valuation Ext", "Custom COGS calculation",       "High",   "SCM IT",     "Active"],
    ])


def _seed_controls(wb):
    _write_rows(wb["Controls"], [
        ["CTL_001", "Segregation of Duties",    "Payables",  "SOX",        "Quarterly",  "Internal Audit", "2024-06-30", "Active"],
        ["CTL_002", "Period Close Checklist",   "GL",        "Operational","Monthly",    "Controller",     "2024-08-31", "Active"],
        ["CTL_003", "User Access Review",       "HCM",       "SOX",        "Semi-Annual","Security Team",  "2024-06-01", "Active"],
        ["CTL_004", "Bank Reconciliation",      "Payables",  "SOX",        "Monthly",    "Treasury",       "2024-08-31", "Active"],
    ])


def _seed_test_cases(wb):
    _write_rows(wb["Test_Cases"], [
        ["TC_001", "AP Invoice 2-Way Match",  "Payables", "Regression", "High",   "N", "QA Team", "Active"],
        ["TC_002", "HCM Worker REST API",     "HCM",      "Integration","Critical","Y", "QA Team", "Active"],
        ["TC_003", "GL Period Close",         "GL",       "Regression", "High",   "N", "QA Team", "Active"],
        ["TC_004", "SCM Inventory Opt-In",    "SCM",      "UAT",        "Medium", "N", "QA Team", "Active"],
        ["TC_005", "Security Role Audit",     "Security", "Compliance", "High",   "N", "Security","Active"],
    ])


def _seed_dependencies(wb):
    _write_rows(wb["Dependencies"], [
        ["DEP_001", "Change",    _CHANGE_IDS[0], "Configuration", "CFG_001", "Impacts",   "Matching tolerance may need review"],
        ["DEP_002", "Change",    _CHANGE_IDS[1], "Interface",     "INT_002", "Breaking",  "REST schema change breaks HCM-AD sync"],
        ["DEP_003", "Interface", "INT_001",       "Job",           "JOB_003", "Sequence",  "Payroll job depends on ERP interface"],
    ])


def _seed_remediation_actions(wb):
    _write_rows(wb["Remediation_Actions"], [
        ["ACT_001", "ASMT_001", "Update AP matching config to align with new validation rules",
         "Configuration", "AP Manager", "2024-10-15", "High", "Open"],
        ["ACT_002", "ASMT_002", "Update HCM-AD integration to handle new REST schema",
         "Technical",     "Integration Lead", "2024-10-01", "Critical", "In Progress"],
        ["ACT_003", "ASMT_003", "Evaluate SCM inventory opt-in feature for adoption",
         "Functional",    "SCM Manager", "2024-11-01", "Low", "Open"],
    ])


def _seed_review_log(wb):
    _write_rows(wb["Review_Log"], [
        ["REV_001", "Impact_Assessment", "ASMT_001", "Jane Smith", "2024-09-25", "Approved", "Reviewed and accepted", "Approved"],
        ["REV_002", "Impact_Assessment", "ASMT_002", "John Lee",   "2024-09-26", "Rejected", "Needs more detail",     "Rejected"],
        ["REV_003", "Design_Decision",   "DD_001",   "CTO",        "2024-09-20", "Approved", "Approved for 24C",      "Approved"],
    ])


def _seed_requirements_traceability(wb):
    _write_rows(wb["Requirements_Traceability"], [
        ["REQ_001", "AP Matching Tolerance Config", "Payables", "DD_002", "TC_001", "",       "Active"],
        ["REQ_002", "HCM REST API Integration",     "HCM",      "DD_003", "TC_002", "DEF_001","Active"],
        ["REQ_003", "SCM Inventory Real-Time Track", "SCM",     "DD_004", "TC_004", "",       "Active"],
    ])


def _seed_fit_gap_assessment(wb):
    _write_rows(wb["Fit_Gap_Assessment"], [
        ["FG_001", "BP_001", "3-Way PO Match",          "Partial", "Native only supports 2-way",     "Configuration",  "High",   "Open"],
        ["FG_002", "BP_002", "Custom Bonus Calculation", "Gap",     "No standard formula equivalent",  "Extension",      "Medium", "Resolved"],
        ["FG_003", "BP_004", "Multi-currency Revaluation","Fit",    "Fully covered by Oracle standard", "None",          "Low",    "Closed"],
    ])


def _seed_design_decisions(wb):
    _write_rows(wb["Design_Decisions"], [
        ["DD_001", "Payables",  "Invoice Matching Strategy",
         "Use Oracle native 2-way match with custom tolerance",
         "Minimise customisation risk", "Solution Architect", "2024-08-01", "Approved"],
        ["DD_002", "HCM",       "REST API Versioning Strategy",
         "Pin integration to v22 REST API; migrate to v24 post-upgrade",
         "Reduce upgrade risk", "Integration Architect", "2024-08-15", "Approved"],
        ["DD_003", "SCM",       "Inventory Opt-In Adoption",
         "Defer real-time inventory opt-in to 25A release cycle",
         "Insufficient testing time in 24C window", "SCM Lead", "2024-09-01", "Approved"],
    ])


def _seed_otbi_inventory(wb):
    _write_rows(wb["OTBI_Inventory"], [
        ["OTB_001", "Payables - Invoices",     "AP Manager",   "Critical", "AP_REPORT_ROLE",  "2024-06-01"],
        ["OTB_002", "HCM - Workforce Summary", "HR Director",  "High",     "HCM_REPORT_ROLE", "2024-06-01"],
        ["OTB_003", "GL - Trial Balance",      "Controller",   "Critical", "GL_REPORT_ROLE",  "2024-06-01"],
        ["OTB_004", "SCM - Inventory Ageing",  "SCM Manager",  "Medium",   "SCM_REPORT_ROLE", "2024-06-01"],
    ])


def _seed_bip_reports(wb):
    _write_rows(wb["BIP_Reports"], [
        ["BIP_001", "AP Payment Remittance",    "Payables", "AP Manager",   "Critical", "AP_REPORT_ROLE",  "2024-06-01", "Active"],
        ["BIP_002", "Payslip Report",           "HCM",      "HR Director",  "High",     "HCM_REPORT_ROLE", "2024-06-01", "Active"],
        ["BIP_003", "GL Journal Report",        "GL",       "Controller",   "High",     "GL_REPORT_ROLE",  "2024-06-01", "Active"],
    ])


def _seed_hdl_fbdi_loads(wb):
    _write_rows(wb["HDL_FBDI_Loads"], [
        ["LOAD_001", "Worker",          "HDL",  "Validated", 0,   "workers_20240901.dat",  "2024-09-01"],
        ["LOAD_002", "Salary",          "HDL",  "Validated", 2,   "salary_20240901.dat",   "2024-09-01"],
        ["LOAD_003", "Supplier",        "FBDI", "Validated", 0,   "suppliers_20240901.xlsx","2024-09-01"],
        ["LOAD_004", "Journal Entries", "FBDI", "Rejected",  45,  "journals_20240902.xlsx","2024-09-02"],
    ])


def _seed_security_roles(wb):
    _write_rows(wb["Security_Roles"], [
        ["ROL_001", "AP Manager",          "Payables",     "Job",  "Restricted", "2024-06-01", "Finance",   "Active"],
        ["ROL_002", "AP Supervisor",       "Payables",     "Job",  "Full",       "2024-06-01", "Finance",   "Active"],
        ["ROL_003", "HR Analyst",          "HCM",          "Job",  "Restricted", "2024-06-01", "HR Ops",    "Active"],
        ["ROL_004", "IT Security Admin",   "Security",     "Abstract","Full",    "2024-06-01", "IT Security","Active"],
    ])


def _seed_environment_promotions(wb):
    _write_rows(wb["Environment_Promotions"], [
        ["PROM_001", _RELEASE_ID, _ENV_DEV, _ENV_UAT,  "2024-09-10", "Dev Lead",  "Approved", "Initial UAT deploy"],
        ["PROM_002", _RELEASE_ID, _ENV_UAT, _ENV_PROD, "2024-09-20", "IT Ops",    "Approved", "Go-live deploy 24C"],
        ["PROM_003", "REL_24Q4",  _ENV_DEV, _ENV_UAT,  "",           "",          "Pending",  "Planned for Nov 2024"],
    ])


def _seed_cutover_runbook(wb):
    _write_rows(wb["Cutover_Runbook"], [
        ["STEP_001", "Freeze ERP Transactions",   "Finance Ops",  "2h",  "",        "Resume from backup point", "Complete"],
        ["STEP_002", "Run Final HDL Loads",        "IT Ops",       "3h",  "STEP_001","Re-run load files",        "Complete"],
        ["STEP_003", "Execute Smoke Tests",        "QA Team",      "4h",  "STEP_002","Rollback to STEP_001",     "Complete"],
        ["STEP_004", "Go / No-Go Decision",        "Steering",     "1h",  "STEP_003","Invoke rollback plan",     "Complete"],
        ["STEP_005", "Open System to Users",       "IT Ops",       "1h",  "STEP_004","Emergency freeze",         "Complete"],
    ])


def _seed_testing_command_centre(wb):
    _write_rows(wb["Testing_Command_Centre"], [
        ["TRN_001", _RELEASE_ID, "TC_001", "Passed",  "",        "Manual",    "QA Team", "2024-09-12"],
        ["TRN_002", _RELEASE_ID, "TC_002", "Failed",  "DEF_001", "Manual",    "QA Team", "2024-09-12"],
        ["TRN_003", _RELEASE_ID, "TC_003", "Passed",  "",        "Automated", "QA Team", "2024-09-13"],
        ["TRN_004", _RELEASE_ID, "TC_004", "Blocked", "",        "Manual",    "QA Team", "2024-09-13"],
        ["TRN_005", _RELEASE_ID, "TC_005", "Passed",  "",        "Manual",    "Security","2024-09-14"],
    ])


def _seed_defect_analytics(wb):
    _write_rows(wb["Defect_Analytics"], [
        ["DEF_001", _RELEASE_ID, "Critical", "Integration Schema Change", "Integration Team", "",       "Open"],
        ["DEF_002", _RELEASE_ID, "Medium",   "Config Regression",         "AP Team",          "GRP_001","Resolved"],
        ["DEF_003", _RELEASE_ID, "Low",      "UI Label Mismatch",         "QA Team",          "",       "Closed"],
    ])


def _seed_raid_log(wb):
    _write_rows(wb["RAID_Log"], [
        ["RAID_001", "Risk",       "HCM REST API breaking change may delay go-live",
         "Integration downtime", "Integration Lead", "2024-10-01", "Open"],
        ["RAID_002", "Issue",      "DEF_001 unresolved — HCM-AD sync failure",
         "HR data not syncing",  "QA Team",          "2024-09-25", "Open"],
        ["RAID_003", "Assumption", "Oracle 24C released on schedule 20-Sep-2024",
         "Low",                  "PM",               "2024-09-20", "Closed"],
        ["RAID_004", "Dependency", "Workday Payroll upgrade must align with HCM 24C",
         "Payroll gap risk",     "HR Director",      "2024-10-15", "Open"],
    ])


def _seed_release_readiness(wb):
    _write_rows(wb["Release_Readiness"], [
        ["ERP / Finance",  "Y", 0, 0, "Y"],
        ["HCM",            "N", 1, 1, "N"],
        ["SCM",            "Y", 0, 0, "Y"],
        ["Security",       "Y", 0, 0, "Y"],
        ["Integration",    "N", 1, 1, "N"],
    ])


def _seed_integration_topology(wb):
    _write_rows(wb["Integration_Topology"], [
        ["INT_001", "Oracle ERP", "Workday",      "REST",  "Oracle OIC", "High",   "Y"],
        ["INT_002", "Oracle HCM", "Active Dir",   "SCIM",  "Oracle OIC", "High",   "Y"],
        ["INT_003", "HSBC",       "Oracle ERP",   "SFTP",  "Direct",     "Critical","Y"],
        ["INT_004", "Oracle ERP", "Vertex",       "SOAP",  "Oracle OIC", "Medium", "N"],
    ])


def _seed_ai_governance(wb):
    _write_rows(wb["AI_Governance"], [
        ["GPT-4o",         "Release note summarisation",    "Y", "N", "2024-09-01", "Medium", "Y"],
        ["Watson NLP",     "Impact classification",         "Y", "N", "2024-09-01", "Medium", "Y"],
        ["Internal LLM",   "Remediation recommendations",   "Y", "N", "",           "High",   "Y"],
    ])


def _seed_approval_workflow(wb):
    _write_rows(wb["Approval_Workflow"], [
        ["APR_001", "Impact_Assessment", "ASMT_001", "Finance Director", "2024-09-25", "Approved", "Approved for 24C", "Approved"],
        ["APR_002", "Impact_Assessment", "ASMT_002", "CTO",              "2024-09-26", "Pending",  "",                 "Pending"],
        ["APR_003", "Design_Decision",   "DD_001",   "Solution Arch",    "2024-09-20", "Approved", "Accepted",         "Approved"],
    ])


def _seed_deployment_status(wb):
    _write_rows(wb["Deployment_Status"], [
        ["DEPL_001", _RELEASE_ID, _ENV_UAT,  "ERP Core",      "IT Ops",   "2024-09-10", "Passed", "UAT deploy successful"],
        ["DEPL_002", _RELEASE_ID, _ENV_UAT,  "HCM Module",    "IT Ops",   "2024-09-10", "Failed", "DEF_001 blocker"],
        ["DEPL_003", _RELEASE_ID, _ENV_PROD, "ERP Core",      "IT Ops",   "2024-09-20", "Passed", "Go-live successful"],
        ["DEPL_004", _RELEASE_ID, _ENV_PROD, "HCM Module",    "IT Ops",   "2024-09-21", "Passed", "Post-fix deploy"],
    ])


def _seed_data_lineage(wb):
    _write_rows(wb["Data_Lineage"], [
        ["Oracle HCM",  "PER_ALL_PEOPLE_F",      "PERSON_ID",        "Direct copy",          "W_PERSON_D",         "PERSON_WID"],
        ["Oracle ERP",  "AP_INVOICES_ALL",        "INVOICE_AMOUNT",   "Convert to USD",       "W_AP_INVOICE_F",     "INVOICE_AMT_USD"],
        ["Oracle SCM",  "MTL_SYSTEM_ITEMS_B",     "UNIT_COST",        "Multiply by quantity", "W_INVENTORY_F",      "EXTENDED_COST"],
    ])


def _seed_powerquery_control(wb):
    _write_rows(wb["PowerQuery_Control"], [
        ["qry_clients",         "Bronze", "",             1, "Data Engineer", "Y"],
        ["qry_release_changes", "Bronze", "",             2, "Data Engineer", "Y"],
        ["qry_impact_silver",   "Silver", "qry_clients",  3, "Data Engineer", "Y"],
        ["qry_dashboard",       "Gold",   "qry_impact_silver", 4, "BI Lead", "Y"],
    ])


def _seed_refresh_audit(wb):
    _write_rows(wb["Refresh_Audit"], [
        ["EXEC_001", "2024-09-20 08:00:00", "Data Engineer", 1250, 3, "Success"],
        ["EXEC_002", "2024-09-21 08:00:00", "Data Engineer", 1302, 0, "Success"],
        ["EXEC_003", "2024-09-22 08:00:00", "Scheduled Job", 1298, 1, "Warning"],
    ])


def _seed_impact_assessments(wb):
    """Seed three rows so formulas in cols T and U resolve visibly."""
    rows = [
        # Assessment_ID, Client_ID, Release_ID, Change_ID,
        # Impact_Type, Impacted_Entity_Type, Impacted_Entity_ID,
        # Impact_Reason, Direct, Dep, Custom, Security,
        # Biz_Crit, Custom_Score, Integ_Score, Sec_Score, Env_Score,
        # OracleChange_Score(R-formula), History_Score,
        # Total(T-formula), RiskLevel(U-formula),
        # Review_Status, Reviewed_By, Review_Date,
        # Recommended_Action, Test_Required, Remediation_Required
        ["ASMT_001", _CLIENT_ID, _RELEASE_ID, _CHANGE_IDS[0],
         "Functional", "Configuration", "CFG_001",
         "AP matching rules changed", "Y", "N", "N", "N",
         4, 2, 0, 0, 3, None, 3,
         None, None,           # T and U are formula cells
         "Pending Review", "", "", "Review and update config", "Y", "Y"],
        ["ASMT_002", _CLIENT_ID, _RELEASE_ID, _CHANGE_IDS[1],
         "Technical", "Interface", "INT_002",
         "REST API schema breaking change", "Y", "N", "N", "N",
         5, 0, 5, 0, 3, None, 4,
         None, None,
         "Pending Review", "", "", "Update integration consumer", "Y", "Y"],
        ["ASMT_003", _CLIENT_ID, _RELEASE_ID, _CHANGE_IDS[2],
         "Functional", "Configuration", "CFG_002",
         "Opt-in feature — no mandatory action", "N", "N", "N", "N",
         2, 0, 0, 0, 1, None, 1,
         None, None,
         "Approved", "SCM Manager", "2024-09-22", "Monitor", "N", "N"],
    ]
    ws = wb["Impact_Assessments"]
    for r_idx, row in enumerate(rows, start=2):
        for c_idx, val in enumerate(row, start=1):
            # Skip cols R(18), T(20), U(21) — those are formula cells
            if c_idx in (18, 20, 21):
                continue
            ws.cell(row=r_idx, column=c_idx, value=val)


def _seed_scoring_rules_and_severity_map(wb):
    """
    Seed tblScoringRules data rows AND create the tblSeverityMap table
    in columns J-K of the Scoring_Rules sheet.

    tblSeverityMap is referenced by the XLOOKUP formula in
    Impact_Assessments column R.
    """
    ws = wb["Scoring_Rules"]

    # --- tblScoringRules data rows ---
    scoring_rows = [
        ["SR_001", "Business Criticality", "Business_Criticality_Score", "Critical process",   5, 0.25, "2024-01-01", "Active"],
        ["SR_002", "Business Criticality", "Business_Criticality_Score", "High priority",      4, 0.25, "2024-01-01", "Active"],
        ["SR_003", "Business Criticality", "Business_Criticality_Score", "Medium priority",    3, 0.25, "2024-01-01", "Active"],
        ["SR_004", "Business Criticality", "Business_Criticality_Score", "Low priority",       1, 0.25, "2024-01-01", "Active"],
        ["SR_005", "Customization",        "Customization_Score",        "Complex CEMLI",      5, 0.20, "2024-01-01", "Active"],
        ["SR_006", "Customization",        "Customization_Score",        "Simple config",      2, 0.20, "2024-01-01", "Active"],
        ["SR_007", "Integration",          "Integration_Score",          "Real-time critical", 5, 0.15, "2024-01-01", "Active"],
        ["SR_008", "Integration",          "Integration_Score",          "Batch non-critical", 2, 0.15, "2024-01-01", "Active"],
        ["SR_009", "Security",             "Security_Score",             "SOX control",        5, 0.15, "2024-01-01", "Active"],
        ["SR_010", "Environment",          "Environment_Score",          "Prod only",          4, 0.10, "2024-01-01", "Active"],
    ]
    _write_rows(ws, scoring_rows)

    # --- tblSeverityMap in columns J-K ---
    severity_map = [
        ("Severity_Text", "Score"),   # header row
        ("Critical",      5),
        ("High",          4),
        ("Medium",        3),
        ("Low",           1),
        ("Informational", 0),
    ]

    from src.styles import style_header
    for r_idx, (text, score) in enumerate(severity_map, start=1):
        a = ws.cell(row=r_idx, column=10, value=text)
        b = ws.cell(row=r_idx, column=11, value=score)
        if r_idx == 1:
            style_header(a)
            style_header(b)

    # Register as a proper Excel Table
    sev_tbl = Table(
        displayName="tblSeverityMap",
        ref=f"J1:K{len(severity_map)}",
    )
    sev_tbl.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showRowStripes=True,
    )
    ws.add_table(sev_tbl)
    ws.column_dimensions["J"].width = 20
    ws.column_dimensions["K"].width = 10


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def seed_all(wb) -> None:
    """Seed every sheet with demo data."""
    _seed_clients(wb)
    _seed_oracle_releases(wb)
    _seed_release_changes(wb)
    _seed_business_processes(wb)
    _seed_applications(wb)
    _seed_interfaces(wb)
    _seed_jobs_batches(wb)
    _seed_environments(wb)
    _seed_configurations(wb)
    _seed_customizations(wb)
    _seed_controls(wb)
    _seed_test_cases(wb)
    _seed_dependencies(wb)
    _seed_scoring_rules_and_severity_map(wb)
    _seed_impact_assessments(wb)
    _seed_remediation_actions(wb)
    _seed_review_log(wb)
    _seed_requirements_traceability(wb)
    _seed_fit_gap_assessment(wb)
    _seed_design_decisions(wb)
    _seed_otbi_inventory(wb)
    _seed_bip_reports(wb)
    _seed_hdl_fbdi_loads(wb)
    _seed_security_roles(wb)
    _seed_environment_promotions(wb)
    _seed_cutover_runbook(wb)
    _seed_testing_command_centre(wb)
    _seed_defect_analytics(wb)
    _seed_raid_log(wb)
    _seed_release_readiness(wb)
    _seed_integration_topology(wb)
    _seed_ai_governance(wb)
    _seed_approval_workflow(wb)
    _seed_deployment_status(wb)
    _seed_data_lineage(wb)
    _seed_powerquery_control(wb)
    _seed_refresh_audit(wb)
