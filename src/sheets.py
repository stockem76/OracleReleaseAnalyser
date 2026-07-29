"""
sheets.py
---------
Builds the workbook skeleton: all 40 sheets, Excel tables with styled
headers, and per-sheet header rows for non-table sheets.
"""

from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

from src import styles

# ---------------------------------------------------------------------------
# SHEET ORDER
# ---------------------------------------------------------------------------

SHEET_ORDER = [
    "Instructions",
    "Clients",
    "Oracle_Releases",
    "Release_Changes",
    "Business_Processes",
    "Applications",
    "Interfaces",
    "Jobs_Batches",
    "Environments",
    "Configurations",
    "Customizations",
    "Controls",
    "Test_Cases",
    "Dependencies",
    "Scoring_Rules",
    "Impact_Assessments",
    "Remediation_Actions",
    "Executive_Summary",
    "Review_Log",
    "Reference_Lists",
    # Extended governance
    "Metadata_Config",
    "PowerQuery_Control",
    "Data_Lineage",
    "Refresh_Audit",
    # Exceptions
    "Exceptions_Unmapped_Modules",
    "Exceptions_Missing_Criticality",
    "Exceptions_Invalid_Status",
    "Exceptions_Duplicate_IDs",
    # Delivery Digital Thread
    "Requirements_Traceability",
    "Fit_Gap_Assessment",
    "Design_Decisions",
    "OTBI_Inventory",
    "BIP_Reports",
    "HDL_FBDI_Loads",
    "Security_Roles",
    "Environment_Promotions",
    "Cutover_Runbook",
    "Testing_Command_Centre",
    "Defect_Analytics",
    "RAID_Log",
    "Release_Readiness",
    "Integration_Topology",
    "AI_Governance",
    "Approval_Workflow",
    "Deployment_Status",
]

# ---------------------------------------------------------------------------
# TABLE DEFINITIONS (sheets that get a full Excel Table + styled headers)
# ---------------------------------------------------------------------------

TABLES = {
    "Clients": {
        "table_name": "tblClients",
        "columns": [
            "Client_ID", "Client_Name", "Client_Code", "Industry",
            "Region", "Primary_Contact", "Support_Model", "Risk_Profile", "Status",
        ],
    },
    "Business_Processes": {
        "table_name": "tblBusinessProcesses",
        "columns": [
            "Process_ID", "Process_Name", "Module", "Sub_Module",
            "Process_Owner", "Criticality", "Status",
        ],
    },
    "Applications": {
        "table_name": "tblApplications",
        "columns": [
            "App_ID", "App_Name", "App_Type", "Vendor",
            "Version", "Environment", "Criticality", "Status",
        ],
    },
    "Interfaces": {
        "table_name": "tblInterfaces",
        "columns": [
            "Interface_ID", "Interface_Name", "Source_System", "Target_System",
            "Direction", "Protocol", "Frequency", "Criticality", "Status",
        ],
    },
    "Jobs_Batches": {
        "table_name": "tblJobsBatches",
        "columns": [
            "Job_ID", "Job_Name", "Schedule", "Module",
            "Run_As_User", "Criticality", "Last_Run_Date", "Status",
        ],
    },
    "Environments": {
        "table_name": "tblEnvironments",
        "columns": [
            "Env_ID", "Env_Name", "Env_Type", "Oracle_Product",
            "URL", "Refresh_Cadence", "Owner", "Status",
        ],
    },
    "Configurations": {
        "table_name": "tblConfigurations",
        "columns": [
            "Config_ID", "Module", "Config_Area", "Config_Name",
            "Config_Value", "Last_Changed_Date", "Changed_By", "Status",
        ],
    },
    "Customizations": {
        "table_name": "tblCustomizations",
        "columns": [
            "Custom_ID", "Module", "Object_Type", "Object_Name",
            "Description", "Complexity", "Owner", "Status",
        ],
    },
    "Controls": {
        "table_name": "tblControls",
        "columns": [
            "Control_ID", "Control_Name", "Module", "Control_Type",
            "Frequency", "Owner", "Last_Tested_Date", "Status",
        ],
    },
    "Test_Cases": {
        "table_name": "tblTestCases",
        "columns": [
            "Test_Case_ID", "Test_Name", "Module", "Test_Type",
            "Priority", "Automation_Flag", "Owner", "Status",
        ],
    },
    "Dependencies": {
        "table_name": "tblDependencies",
        "columns": [
            "Dependency_ID", "From_Entity_Type", "From_Entity_ID",
            "To_Entity_Type", "To_Entity_ID", "Dependency_Type", "Notes",
        ],
    },
    "Scoring_Rules": {
        "table_name": "tblScoringRules",
        "columns": [
            "Rule_ID", "Rule_Name", "Dimension", "Condition",
            "Score", "Weight", "Effective_Date", "Status",
        ],
    },
    "Remediation_Actions": {
        "table_name": "tblRemediationActions",
        "columns": [
            "Action_ID", "Assessment_ID", "Action_Description", "Action_Type",
            "Owner", "Due_Date", "Priority", "Status",
        ],
    },
    "Review_Log": {
        "table_name": "tblReviewLog",
        "columns": [
            "Review_ID", "Entity_Type", "Entity_ID", "Reviewer",
            "Review_Date", "Decision", "Comments", "Status",
        ],
    },
    "Requirements_Traceability": {
        "table_name": "tblRequirementsTraceability",
        "columns": [
            "Req_ID", "Requirement_Name", "Module", "Design_ID",
            "Test_Case_ID", "Defect_ID", "Status",
        ],
    },
    "Fit_Gap_Assessment": {
        "table_name": "tblFitGapAssessment",
        "columns": [
            "FitGap_ID", "Process_ID", "Requirement", "Oracle_Coverage",
            "Gap_Description", "Resolution_Type", "Priority", "Status",
        ],
    },
    "Design_Decisions": {
        "table_name": "tblDesignDecisions",
        "columns": [
            "Decision_ID", "Module", "Decision_Title", "Decision_Description",
            "Rationale", "Decision_Owner", "Decision_Date", "Status",
        ],
    },
    "BIP_Reports": {
        "table_name": "tblBIPReports",
        "columns": [
            "Report_ID", "Report_Name", "Module", "Owner",
            "Criticality", "Security_Role", "Last_Reviewed", "Status",
        ],
    },
    "Security_Roles": {
        "table_name": "tblSecurityRoles",
        "columns": [
            "Role_ID", "Role_Name", "Module", "Role_Type",
            "Data_Access_Level", "Last_Reviewed", "Owner", "Status",
        ],
    },
    "Environment_Promotions": {
        "table_name": "tblEnvironmentPromotions",
        "columns": [
            "Promotion_ID", "Release_ID", "From_Env", "To_Env",
            "Promotion_Date", "Promoted_By", "Approval_Status", "Notes",
        ],
    },
    "Cutover_Runbook": {
        "table_name": "tblCutoverRunbook",
        "columns": [
            "Step_ID", "Step_Name", "Responsible_Team", "Estimated_Duration",
            "Dependencies", "Rollback_Procedure", "Status",
        ],
    },
    "Approval_Workflow": {
        "table_name": "tblApprovalWorkflow",
        "columns": [
            "Approval_ID", "Entity_Type", "Entity_ID", "Approver",
            "Approval_Date", "Decision", "Comments", "Status",
        ],
    },
    "Deployment_Status": {
        "table_name": "tblDeploymentStatus",
        "columns": [
            "Deployment_ID", "Release_ID", "Environment", "Component",
            "Deployed_By", "Deployment_Date", "Validation_Status", "Notes",
        ],
    },
    "Oracle_Releases": {
        "table_name": "tblOracleReleases",
        "columns": [
            "Release_ID", "Release_Name", "Release_Year", "Release_Quarter",
            "Oracle_Product", "Release_Date", "Notes_Source_URL",
            "Ingestion_Date", "Status",
        ],
    },
    "Release_Changes": {
        "table_name": "tblReleaseChanges",
        "columns": [
            "Change_ID", "Release_ID", "Change_Title", "Change_Description",
            "Oracle_Module", "Feature_Area", "Change_Type", "Technical_Object",
            "API_Service", "Config_Area", "Security_Flag", "Compliance_Flag",
            "Deprecation_Flag", "Required_Action", "Oracle_Severity",
            "Effective_Date", "Source_Reference", "Source_Section",
        ],
    },
    "Impact_Assessments": {
        "table_name": "tblImpactAssessments",
        "columns": [
            "Assessment_ID", "Client_ID", "Release_ID", "Change_ID",
            "Impact_Type", "Impacted_Entity_Type", "Impacted_Entity_ID",
            "Impact_Reason", "Direct_Match_Flag", "Dependency_Match_Flag",
            "Customization_Match_Flag", "Security_Impact_Flag",
            "Business_Criticality_Score", "Customization_Score",
            "Integration_Score", "Security_Score", "Environment_Score",
            "Oracle_Change_Score", "History_Score", "Total_Risk_Score",
            "Risk_Level", "Review_Status", "Reviewed_By", "Review_Date",
            "Recommended_Action", "Test_Required_Flag", "Remediation_Required_Flag",
        ],
    },
}

# ---------------------------------------------------------------------------
# PER-SHEET HEADER DEFINITIONS (sheets that get plain styled headers only)
# ---------------------------------------------------------------------------

PLAIN_HEADERS = {
    "AI_Governance": [
        "Model_Name", "Use_Case", "Human_Approval_Required",
        "Production_Approved", "Validation_Date", "Risk_Level", "Audit_Required",
    ],
    "RAID_Log": [
        "RAID_ID", "Type", "Description", "Impact",
        "Owner", "Due_Date", "Status",
    ],
    "Testing_Command_Centre": [
        "Test_Run_ID", "Release_ID", "Test_Case_ID", "Execution_Status",
        "Defect_Link", "Automation_Status", "Executed_By", "Execution_Date",
    ],
    "Defect_Analytics": [
        "Defect_ID", "Release_ID", "Severity", "Root_Cause",
        "Assigned_Team", "Duplicate_Group", "Status",
    ],
    "OTBI_Inventory": [
        "Report_ID", "Subject_Area", "Owner",
        "Criticality", "Security_Role", "Last_Reviewed",
    ],
    "HDL_FBDI_Loads": [
        "Load_ID", "Object_Name", "Load_Type", "Validation_Status",
        "Rejected_Records", "Source_File", "Last_Load_Date",
    ],
    "Integration_Topology": [
        "Integration_ID", "Source_System", "Target_System",
        "Protocol", "Middleware", "Criticality", "Monitoring_Enabled",
    ],
    "Release_Readiness": [
        "Domain", "Testing_Complete", "Defects_Open",
        "Critical_Risks", "Deployment_Ready",
    ],
    "Data_Lineage": [
        "Source_System", "Source_Object", "Source_Field",
        "Transformation_Rule", "Target_Table", "Target_Field",
    ],
    "PowerQuery_Control": [
        "Query_Name", "Layer", "Depends_On",
        "Refresh_Order", "Owner", "Active",
    ],
    "Refresh_Audit": [
        "Execution_ID", "Timestamp", "Executed_By",
        "Rows_Processed", "Exceptions_Found", "Execution_Status",
    ],
    # Exception tabs all share the same four columns
    "Exceptions_Unmapped_Modules":    ["Exception_Type", "Record_ID", "Description", "Detected_Date"],
    "Exceptions_Missing_Criticality": ["Exception_Type", "Record_ID", "Description", "Detected_Date"],
    "Exceptions_Invalid_Status":      ["Exception_Type", "Record_ID", "Description", "Detected_Date"],
    "Exceptions_Duplicate_IDs":       ["Exception_Type", "Record_ID", "Description", "Detected_Date"],
}


# ---------------------------------------------------------------------------
# Column width helpers
# ---------------------------------------------------------------------------

# Minimum and maximum column widths (characters)
_MIN_COL_WIDTH = 12
_MAX_COL_WIDTH = 50

# Per-column overrides: header name → fixed width (takes precedence over auto-fit)
_COLUMN_WIDTH_OVERRIDES: dict[str, int] = {
    "Change_Description": 50,
    "Impact_Reason":       50,
    "Description":         50,
    "Notes":               40,
    "Rollback_Procedure":  40,
}


def _auto_width(header: str) -> int:
    """Return an appropriate column width for the given header string."""
    if header in _COLUMN_WIDTH_OVERRIDES:
        return _COLUMN_WIDTH_OVERRIDES[header]
    # Base width = header length + padding; clamp to min/max
    return max(_MIN_COL_WIDTH, min(len(header) + 4, _MAX_COL_WIDTH))


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def build_workbook(config: dict) -> Workbook:
    """Create and return the fully-structured workbook.

    All sheets are created, Excel Tables applied to TABLES sheets,
    plain styled headers applied to PLAIN_HEADERS sheets, and freeze
    panes set on every sheet that has data.

    Column widths are auto-fitted to the header text length (clamped to
    12–50 characters) with per-column overrides for long-text fields.
    """
    max_rows = config["max_rows"]

    wb = Workbook()
    wb.remove(wb.active)  # Remove default empty sheet

    for name in SHEET_ORDER:
        wb.create_sheet(name)

    # --- Excel Table sheets ---
    for sheet_name, cfg in TABLES.items():
        ws = wb[sheet_name]
        columns = cfg["columns"]

        for idx, col_name in enumerate(columns, start=1):
            c = ws.cell(row=1, column=idx)
            c.value = col_name
            styles.style_header(c)
            ws.column_dimensions[get_column_letter(idx)].width = _auto_width(col_name)

        end_col = get_column_letter(len(columns))
        tbl = Table(
            displayName=cfg["table_name"],
            ref=f"A1:{end_col}{max_rows}",
        )
        tbl.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2",
            showRowStripes=True,
        )
        ws.add_table(tbl)
        ws.freeze_panes = "A2"

    # --- Plain header sheets ---
    for sheet_name, headers in PLAIN_HEADERS.items():
        ws = wb[sheet_name]
        for idx, h in enumerate(headers, start=1):
            c = ws.cell(row=1, column=idx)
            c.value = h
            styles.style_header(c)
            ws.column_dimensions[get_column_letter(idx)].width = _auto_width(h)

    return wb
