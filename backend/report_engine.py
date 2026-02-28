import os
import json
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from backend.drift_engine import compute_policy_drift
from backend.timeline_engine import compute_timeline_drift


def generate_audit_report(company_name):

    filename = f"{company_name}_Consent_Audit_Report.pdf"
    filepath = os.path.join("backend", filename)

    doc = SimpleDocTemplate(filepath)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("Consent Decay Detector Report", styles["Heading1"]))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(f"Company: {company_name}", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph(f"Generated: {datetime.now()}", styles["Normal"]))
    elements.append(Spacer(1, 0.5 * inch))

    baseline = compute_policy_drift(company_name, "baseline", True)
    incremental = compute_policy_drift(company_name, "incremental", True)
    timeline = compute_timeline_drift(company_name, True)

    elements.append(Paragraph("Baseline Analysis", styles["Heading2"]))
    elements.append(Preformatted(json.dumps(baseline, indent=2), styles["Code"]))
    elements.append(Spacer(1, 0.5 * inch))

    elements.append(Paragraph("Incremental Analysis", styles["Heading2"]))
    elements.append(Preformatted(json.dumps(incremental, indent=2), styles["Code"]))
    elements.append(Spacer(1, 0.5 * inch))

    elements.append(Paragraph("Timeline Analysis", styles["Heading2"]))
    elements.append(Preformatted(json.dumps(timeline, indent=2), styles["Code"]))

    doc.build(elements)

    return filepath


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m backend.report_engine <CompanyName>")
    else:
        path = generate_audit_report(sys.argv[1])
        print(f"\nReport generated at: {path}")