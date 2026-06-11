import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_complex_pdf():
    input_dir = Path("data/input")
    input_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = input_dir / "complex_sample.pdf"
    
    doc = SimpleDocTemplate(
        str(pdf_path), 
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    styles = getSampleStyleSheet()
    
    # Custom styles
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        spaceAfter=10
    )
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=10
    )
    
    story = []
    
    # Document Title
    story.append(Paragraph("Acme Corp Executive Report", styles['Title']))
    story.append(Spacer(1, 15))
    
    # Section 1
    story.append(Paragraph("1. Organizational Structure", h1_style))
    story.append(Paragraph(
        "Below is the hierarchical nesting mapping of departments and their active allocations.",
        body_style
    ))
    
    # Inner Table 1 (Engineering Projects)
    inner_data_1 = [
        ["Project Name", "Lead", "Budget"],
        ["Apollo Project", "Alice", "$1.2M"],
        ["Ares Initiative", "Charlie", "$800K"]
    ]
    inner_table_1 = Table(inner_data_1, colWidths=[100, 60, 60])
    inner_table_1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    
    # Inner Table 2 (Operations Services)
    inner_data_2 = [
        ["Service", "Provider", "SLA"],
        ["Cloud Hosting", "Acme Corp", "99.9%"],
        ["Security Audit", "SafeGuard", "99.99%"]
    ]
    inner_table_2 = Table(inner_data_2, colWidths=[100, 60, 60])
    inner_table_2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))

    # Outer Table nesting the inner tables
    outer_data = [
        ["Department", "Details & Projects"],
        ["Engineering", inner_table_1],
        ["Operations", inner_table_2]
    ]
    
    outer_table = Table(outer_data, colWidths=[120, 240])
    outer_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B4C7E")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#1A3052")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    
    story.append(outer_table)
    story.append(Spacer(1, 15))
    
    # Section 2
    story.append(Paragraph("2. Strategic Goals", h1_style))
    story.append(Paragraph(
        "Operations are supervised by Bob. They manage beta group clients. "
        "Alice manages the Apollo Project and leads strategic operations.",
        body_style
    ))
    
    doc.build(story)
    print(f"Created complex sample PDF at {pdf_path}")

if __name__ == "__main__":
    create_complex_pdf()
