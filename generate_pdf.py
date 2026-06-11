import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def create_sample_pdf():
    input_dir = Path("data/input")
    input_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = input_dir / "sample.pdf"
    
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph("Acme Corp Project Report", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Body
    text = (
        "Alice works for Acme Corp. Bob manages the Engineering department. "
        "Alice leads the Apollo Project, which belongs to the Engineering department."
    )
    story.append(Paragraph(text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    doc.build(story)
    print(f"Created sample PDF at {pdf_path}")

if __name__ == "__main__":
    create_sample_pdf()
