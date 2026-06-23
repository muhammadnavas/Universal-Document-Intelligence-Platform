"""Generate all sample files needed for format testing."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

doc = SimpleDocTemplate("sample_files/sample_invoice.pdf", pagesize=A4)
styles = getSampleStyleSheet()
story = []

title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=24, textColor=colors.HexColor("#1a1a2e"))
h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=14, textColor=colors.HexColor("#2d6a4f"))
normal = styles["Normal"]

story.append(Paragraph("COMMERCIAL INVOICE", title_style))
story.append(Spacer(1, 0.2 * inch))
story.append(Paragraph("Invoice Number: INV-2026-PRU-0099", h1))
story.append(Paragraph("Date: 2026-06-23", normal))
story.append(Paragraph("Due Date: 2026-07-23", normal))
story.append(Spacer(1, 0.2 * inch))
story.append(Paragraph("<b>Bill To:</b>", h1))
story.append(Paragraph("Name: Rahul Mehta", normal))
story.append(Paragraph("Company: Prudential Financial Ltd.", normal))
story.append(Paragraph("Email: rahul.mehta@prudential.com", normal))
story.append(Paragraph("Phone: +91-9988776655", normal))
story.append(Spacer(1, 0.2 * inch))

USD = "USD"
table_data = [
    ["#", "Description", "Qty", "Unit Price", "Total"],
    ["1", "AI Platform License", "1", "12,000 " + USD, "12,000 " + USD],
    ["2", "Data Engineering Services", "3", "5,000 " + USD, "15,000 " + USD],
    ["3", "Cloud Storage (TB)", "10", "200 " + USD, "2,000 " + USD],
    ["4", "Support and Maintenance", "12", "500 " + USD, "6,000 " + USD],
    ["", "", "", "Subtotal", "35,000 " + USD],
    ["", "", "", "Tax (18%)", "6,300 " + USD],
    ["", "", "", "Grand Total", "41,300 " + USD],
]
t = Table(table_data, colWidths=[0.4 * inch, 2.5 * inch, 0.6 * inch, 1.3 * inch, 1.3 * inch])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
    ("FONTNAME", (0, -3), (-1, -1), "Helvetica-Bold"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
]))
story.append(t)
story.append(Spacer(1, 0.3 * inch))
story.append(Paragraph("Payment Method: Bank Transfer | Account: HDFC-XXXX-9901", normal))
story.append(Paragraph("Terms: Net 30 Days", normal))

doc.build(story)
print("PDF created successfully.")
