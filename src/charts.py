"""
charts.py
---------
Builds the Executive Summary dashboard sheet, including KPI cells and
the Risk Distribution pie chart.
"""

from openpyxl.styles import Font
from openpyxl.chart import PieChart, Reference


def build_executive_summary(wb) -> None:
    """Populate the Executive_Summary sheet with KPIs and a pie chart."""
    ws = wb["Executive_Summary"]

    ws["A1"] = "Oracle Fusion Impact Analyzer Dashboard"
    ws["A1"].font = Font(size=16, bold=True)

    ws["A3"] = "Selected Client_ID"
    ws["A4"] = "Selected Release_ID"

    ws["D3"] = "Total Impacted Items"
    ws["E3"] = (
        "=COUNTIFS("
        "tblImpactAssessments[Client_ID],B3,"
        "tblImpactAssessments[Release_ID],B4)"
    )

    ws["D4"] = "Critical Risks"
    ws["E4"] = (
        "=COUNTIFS("
        "tblImpactAssessments[Client_ID],B3,"
        "tblImpactAssessments[Release_ID],B4,"
        'tblImpactAssessments[Risk_Level],"Critical")'
    )

    pie = PieChart()
    labels = Reference(ws, min_col=4, min_row=3, max_row=4)
    data = Reference(ws, min_col=5, min_row=3, max_row=4)
    pie.add_data(data)
    pie.set_categories(labels)
    pie.title = "Risk Distribution"
    ws.add_chart(pie, "H3")
