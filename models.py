from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()


class Company(db.Model):
    """Seller / Company information (singleton row)."""
    __tablename__ = 'company'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, default='')
    address = db.Column(db.String(500), nullable=False, default='')
    rc_no = db.Column(db.String(100), nullable=False, default='')
    if_no = db.Column(db.String(100), nullable=False, default='')
    ar_no = db.Column(db.String(100), nullable=False, default='')
    tel = db.Column(db.String(50), nullable=False, default='')
    fax = db.Column(db.String(50), nullable=False, default='')

    def __repr__(self):
        return f'<Company {self.name}>'


class Client(db.Model):
    """Client / Buyer information."""
    __tablename__ = 'client'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(200), nullable=False, default='')
    rc_no = db.Column(db.String(100), nullable=False, default='')
    nif_no = db.Column(db.String(100), nullable=False, default='')
    nis_no = db.Column(db.String(100), nullable=False, default='')
    art_no = db.Column(db.String(100), nullable=False, default='')
    tel = db.Column(db.String(50), nullable=False, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoices = db.relationship('Invoice', backref='client', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Client {self.name}>'


class Product(db.Model):
    """Product catalog."""
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    default_tva = db.Column(db.Float, nullable=False, default=19.0)
    default_price = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Product {self.name}>'


class Invoice(db.Model):
    """Invoice header."""
    __tablename__ = 'invoice'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(10), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    total_ht = db.Column(db.Float, nullable=False, default=0.0)
    total_tva = db.Column(db.Float, nullable=False, default=0.0)
    net_a_payer = db.Column(db.Float, nullable=False, default=0.0)
    amount_in_words = db.Column(db.Text, nullable=False, default='')
    payment_terms = db.Column(db.String(100), nullable=False, default='REGLEE A TERME')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('InvoiceItem', backref='invoice', lazy=True,
                            cascade='all, delete-orphan', order_by='InvoiceItem.id')

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'


class InvoiceItem(db.Model):
    """Individual line item on an invoice."""
    __tablename__ = 'invoice_item'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    tva_rate = db.Column(db.Float, nullable=False, default=19.0)
    nbr_co = db.Column(db.Integer, nullable=False, default=1)
    quantity = db.Column(db.Float, nullable=False, default=0.0)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    total_ht = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f'<InvoiceItem {self.product_name}>'
