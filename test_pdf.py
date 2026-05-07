import io
from xhtml2pdf import pisa
from flask import Flask, render_template
from app import app, db, get_company
from models import Invoice

with app.app_context():
    invoice = Invoice.query.first()
    company = get_company()
    html = render_template('invoice_view.html', invoice=invoice, company=company, is_pdf=True)
    result = io.BytesIO()
    pdf = pisa.CreatePDF(io.StringIO(html), dest=result, encoding='utf-8')
    if pdf.err:
        print("PDF Error:", pdf.err)
    else:
        print("PDF Success")
        with open("test.pdf", "wb") as f:
            f.write(result.getvalue())
