#!/usr/bin/env python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

# Create a simple 2-page PDF
pdf_path = 'test_upload.pdf'
c = canvas.Canvas(pdf_path, pagesize=letter)

# Page 1
c.drawString(100, 750, 'Page 1 - DNI')
c.showPage()

# Page 2
c.drawString(100, 750, 'Page 2 - Curriculum')
c.showPage()

c.save()
print(f'PDF creado: {os.path.abspath(pdf_path)}')
