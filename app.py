import io
import json
from datetime import date, datetime

from flask import (Flask, render_template, request, redirect, url_for,
                   flash, jsonify, make_response)
from num2words import num2words

from flask_wtf.csrf import CSRFProtect

from config import Config
from models import db, Company, Client, Product, Invoice, InvoiceItem

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
csrf = CSRFProtect(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def amount_to_words(amount):
    """Convert a numeric amount to uppercase French words + DINARS."""
    integer_part = int(round(amount))
    if integer_part == 0:
        return "ZERO DINARS"
    words = num2words(integer_part, lang='fr').upper()
    # Clean up hyphens for readability matching the sample
    words = words.replace('-', ' ')
    return f"{words} DINARS"


def get_next_invoice_number():
    """Return the next auto‑incremented invoice number as a zero‑padded string."""
    last = Invoice.query.order_by(Invoice.id.desc()).first()
    if last:
        try:
            next_num = int(last.invoice_number) + 1
        except ValueError:
            next_num = 1
    else:
        next_num = 1
    return str(next_num).zfill(6)


def get_company():
    """Return the singleton Company row, creating it if necessary."""
    company = Company.query.first()
    if not company:
        company = Company(
            name='EURL MTEG FOOD      ……',
            address='CITE KASNAF LOT Nᵒ515 GUE CONSTANTINE',
            rc_no='16/00-1204232',
            if_no='002416120423298\n00.99.00.01.98',
            ar_no='16268751524',
            tel='0000.00.00.00',
            fax='0000.00.00.00',
        )
        db.session.add(company)
        db.session.commit()
    return company


def format_number(value, decimals=2):
    """Format number with thousands separator and decimal places."""
    if value is None:
        return '0.00'
    return f"{value:,.{decimals}f}".replace(',', ' ').replace('.', ',') if False else f"{value:,.{decimals}f}"


# Register template helpers
app.jinja_env.globals.update(format_number=format_number)


# ---------------------------------------------------------------------------
# Routes — Dashboard
# ---------------------------------------------------------------------------

@app.route('/')
def dashboard():
    company = get_company()
    recent_invoices = Invoice.query.order_by(Invoice.date.desc(), Invoice.id.desc()).limit(10).all()
    total_invoices = Invoice.query.count()
    total_clients = Client.query.count()
    total_revenue = db.session.query(db.func.sum(Invoice.net_a_payer)).scalar() or 0
    return render_template('dashboard.html',
                           company=company,
                           recent_invoices=recent_invoices,
                           total_invoices=total_invoices,
                           total_clients=total_clients,
                           total_revenue=total_revenue)


# ---------------------------------------------------------------------------
# Routes — Company
# ---------------------------------------------------------------------------

@app.route('/company/edit', methods=['GET', 'POST'])
def company_edit():
    company = get_company()
    if request.method == 'POST':
        company.name = request.form.get('name', '')
        company.address = request.form.get('address', '')
        company.rc_no = request.form.get('rc_no', '')
        company.if_no = request.form.get('if_no', '')
        company.ar_no = request.form.get('ar_no', '')
        company.tel = request.form.get('tel', '')
        company.fax = request.form.get('fax', '')
        db.session.commit()
        flash('Informations de la société mises à jour.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('company_edit.html', company=company)


# ---------------------------------------------------------------------------
# Routes — Clients
# ---------------------------------------------------------------------------

@app.route('/clients')
def clients():
    all_clients = Client.query.order_by(Client.name).all()
    return render_template('clients.html', clients=all_clients)


@app.route('/clients/new', methods=['GET', 'POST'])
def client_new():
    if request.method == 'POST':
        client = Client(
            name=request.form.get('name', ''),
            city=request.form.get('city', ''),
            rc_no=request.form.get('rc_no', ''),
            nif_no=request.form.get('nif_no', ''),
            nis_no=request.form.get('nis_no', ''),
            art_no=request.form.get('art_no', ''),
            tel=request.form.get('tel', ''),
        )
        db.session.add(client)
        db.session.commit()
        flash(f'Client « {client.name} » ajouté.', 'success')
        return redirect(url_for('clients'))
    return render_template('client_form.html', client=None)


@app.route('/clients/<int:id>/edit', methods=['GET', 'POST'])
def client_edit(id):
    client = Client.query.get_or_404(id)
    if request.method == 'POST':
        client.name = request.form.get('name', '')
        client.city = request.form.get('city', '')
        client.rc_no = request.form.get('rc_no', '')
        client.nif_no = request.form.get('nif_no', '')
        client.nis_no = request.form.get('nis_no', '')
        client.art_no = request.form.get('art_no', '')
        client.tel = request.form.get('tel', '')
        db.session.commit()
        flash(f'Client « {client.name} » mis à jour.', 'success')
        return redirect(url_for('clients'))
    return render_template('client_form.html', client=client)


@app.route('/clients/<int:id>/delete', methods=['POST'])
def client_delete(id):
    client = Client.query.get_or_404(id)
    name = client.name
    db.session.delete(client)
    db.session.commit()
    flash(f'Client « {name} » supprimé.', 'warning')
    return redirect(url_for('clients'))


# ---------------------------------------------------------------------------
# Routes — Products
# ---------------------------------------------------------------------------

@app.route('/products')
def products():
    all_products = Product.query.order_by(Product.name).all()
    return render_template('products.html', products=all_products)


@app.route('/products/new', methods=['GET', 'POST'])
def product_new():
    if request.method == 'POST':
        product = Product(
            name=request.form.get('name', ''),
            default_tva=float(request.form.get('default_tva', 19)),
            default_price=float(request.form.get('default_price', 0)),
        )
        db.session.add(product)
        db.session.commit()
        flash(f'Produit « {product.name} » ajouté.', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', product=None)


@app.route('/products/<int:id>/edit', methods=['GET', 'POST'])
def product_edit(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form.get('name', '')
        product.default_tva = float(request.form.get('default_tva', 19))
        product.default_price = float(request.form.get('default_price', 0))
        db.session.commit()
        flash(f'Produit « {product.name} » mis à jour.', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', product=product)


@app.route('/products/<int:id>/delete', methods=['POST'])
def product_delete(id):
    product = Product.query.get_or_404(id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'Produit « {name} » supprimé.', 'warning')
    return redirect(url_for('products'))


# ---------------------------------------------------------------------------
# Routes — Invoices
# ---------------------------------------------------------------------------

@app.route('/invoices')
def invoices():
    all_invoices = Invoice.query.order_by(Invoice.date.desc(), Invoice.id.desc()).all()
    return render_template('invoice_list.html', invoices=all_invoices)


@app.route('/invoices/new', methods=['GET', 'POST'])
def invoice_new():
    if request.method == 'POST':
        return _save_invoice(None)

    clients = Client.query.order_by(Client.name).all()
    all_products = Product.query.order_by(Product.name).all()
    next_number = get_next_invoice_number()
    return render_template('invoice_form.html',
                           invoice=None,
                           clients=clients,
                           products=all_products,
                           next_number=next_number,
                           today=date.today().strftime('%Y-%m-%d'))


@app.route('/invoices/<int:id>/edit', methods=['GET', 'POST'])
def invoice_edit(id):
    invoice = Invoice.query.get_or_404(id)
    if request.method == 'POST':
        return _save_invoice(invoice)

    clients = Client.query.order_by(Client.name).all()
    all_products = Product.query.order_by(Product.name).all()
    return render_template('invoice_form.html',
                           invoice=invoice,
                           clients=clients,
                           products=all_products,
                           next_number=invoice.invoice_number,
                           today=invoice.date.strftime('%Y-%m-%d'))


def _save_invoice(invoice):
    """Create or update an invoice from form data."""
    is_new = invoice is None
    if is_new:
        invoice = Invoice()

    invoice.invoice_number = request.form.get('invoice_number', get_next_invoice_number())
    invoice.date = datetime.strptime(request.form.get('date', ''), '%Y-%m-%d').date()
    invoice.client_id = int(request.form.get('client_id'))
    invoice.payment_terms = request.form.get('payment_terms', 'REGLEE A TERME')

    # Clear existing items for update
    if not is_new:
        InvoiceItem.query.filter_by(invoice_id=invoice.id).delete()

    # Collect items from form
    product_names = request.form.getlist('product_name[]')
    tva_rates = request.form.getlist('tva_rate[]')
    nbr_cos = request.form.getlist('nbr_co[]')
    quantities = request.form.getlist('quantity[]')
    unit_prices = request.form.getlist('unit_price[]')

    total_ht = 0.0
    items = []
    for i in range(len(product_names)):
        if not product_names[i].strip():
            continue
        qty = float(quantities[i]) if quantities[i] else 0
        price = float(unit_prices[i]) if unit_prices[i] else 0
        item_total = qty * price
        total_ht += item_total

        item = InvoiceItem(
            product_name=product_names[i],
            tva_rate=float(tva_rates[i]) if tva_rates[i] else 19,
            nbr_co=int(nbr_cos[i]) if nbr_cos[i] else 1,
            quantity=qty,
            unit_price=price,
            total_ht=item_total,
        )
        items.append(item)

    # Calculate totals — use weighted average TVA from items
    if items:
        # Calculate TVA per item based on its own rate
        total_tva = sum(item.total_ht * (item.tva_rate / 100) for item in items)
    else:
        total_tva = 0.0

    net_a_payer = total_ht + total_tva

    invoice.total_ht = total_ht
    invoice.total_tva = total_tva
    invoice.net_a_payer = net_a_payer
    invoice.amount_in_words = amount_to_words(net_a_payer)

    if is_new:
        db.session.add(invoice)
    db.session.flush()  # Ensure invoice.id is available

    for item in items:
        item.invoice_id = invoice.id
        db.session.add(item)

    db.session.commit()
    flash(f'Facture N° {invoice.invoice_number} enregistrée.', 'success')
    return redirect(url_for('invoice_view', id=invoice.id))


@app.route('/invoices/<int:id>')
def invoice_view(id):
    invoice = Invoice.query.get_or_404(id)
    company = get_company()
    return render_template('invoice_view.html', invoice=invoice, company=company)


@app.route('/invoices/<int:id>/delete', methods=['POST'])
def invoice_delete(id):
    invoice = Invoice.query.get_or_404(id)
    num = invoice.invoice_number
    db.session.delete(invoice)
    db.session.commit()
    flash(f'Facture N° {num} supprimée.', 'warning')
    return redirect(url_for('invoices'))


@app.route('/invoices/<int:id>/pdf')
def invoice_pdf(id):
    invoice = Invoice.query.get_or_404(id)
    company = get_company()
    html = render_template('invoice_view.html', invoice=invoice, company=company, is_pdf=True)

    try:
        from xhtml2pdf import pisa
        result = io.BytesIO()
        pdf = pisa.CreatePDF(io.StringIO(html), dest=result, encoding='utf-8')
        if not pdf.err:
            response = make_response(result.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = \
                f'inline; filename=facture_{invoice.invoice_number}.pdf'
            return response
    except ImportError:
        pass

    flash('Erreur lors de la génération du PDF. Vérifiez que xhtml2pdf est installé.', 'danger')
    return redirect(url_for('invoice_view', id=id))


# ---------------------------------------------------------------------------
# API endpoints (for JavaScript)
# ---------------------------------------------------------------------------

@app.route('/api/products/<int:id>')
def api_product(id):
    product = Product.query.get_or_404(id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'default_tva': product.default_tva,
        'default_price': product.default_price,
    })


@app.route('/api/next-invoice-number')
def api_next_invoice_number():
    return jsonify({'next_number': get_next_invoice_number()})


# ---------------------------------------------------------------------------
# Database initialization & seed data
# ---------------------------------------------------------------------------

def seed_data():
    """Seed company info and sample data if the database is empty."""
    get_company()  # Creates default company if not exists

    # Seed sample products if none exist
    if Product.query.count() == 0:
        products = [
            Product(name='ARACHID BL', default_tva=19.0, default_price=265.00),
            Product(name='PISTACH 07.12.24', default_tva=19.0, default_price=1880.00),
            Product(name='SESAM 02.02.23', default_tva=19.0, default_price=280.00),
        ]
        db.session.add_all(products)
        db.session.commit()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True, port=5000)
