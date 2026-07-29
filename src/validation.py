"""
validation.py
-------------
Applies Excel DataValidation dropdowns to the Impact_Assessments sheet.
Depends on DefinedNames registered by reference_lists.populate_reference_lists().
"""

from openpyxl.worksheet.datavalidation import DataValidation


def apply_validations(wb, config: dict) -> None:
    """Add list-based DataValidation rules to Impact_Assessments."""
    max_rows = config["max_rows"]
    ws = wb["Impact_Assessments"]

    # Risk Level — column U
    risk_dv = DataValidation(type="list", formula1="=lstRiskLevels")
    ws.add_data_validation(risk_dv)
    risk_dv.add(f"U2:U{max_rows}")

    # Review Status — column V
    review_dv = DataValidation(type="list", formula1="=lstReviewStatus")
    ws.add_data_validation(review_dv)
    review_dv.add(f"V2:V{max_rows}")

    # Yes/No flags — columns Z and AA
    yesno_dv = DataValidation(type="list", formula1="=lstYesNo")
    ws.add_data_validation(yesno_dv)
    yesno_dv.add(f"Z2:AA{max_rows}")
