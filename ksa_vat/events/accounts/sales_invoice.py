import frappe
from frappe import _
from frappe.utils.data import add_to_date, get_time, getdate
from erpnext import get_region
from pyqrcode import create as qr_create
import io
import os
from base64 import b64encode


def create_qr_code(doc, method):
    """Create QR Code after inserting Sales Inv
    """

    region = get_region(doc.company)
    if region not in ['Saudi Arabia']:
        return

    # if QR Code field not present, do nothing
    if not hasattr(doc, 'qr_code'):
        return

    # Don't create QR Code if it already exists
    qr_code = doc.get("qr_code")
    if qr_code and frappe.db.exists({"doctype": "File", "file_url": qr_code}):
        return

    fields = frappe.get_meta('Sales Invoice').fields

    for field in fields:
        if field.fieldname == 'qr_code' and field.fieldtype == 'Attach Image':
            # Creating qr code
            '''
            1. Seller's Name
            2. VAT Number
            3. Time Stamp
            4. VAT Amount
            5. Invoice Amount
            6. Customer's Name
            7. Customer VAT ID
            '''
            # QR String
            qr_string = ""

            # Sellers Name
            seller_name = f"Seller name: {doc.company}"

            # VAT Number
            tax_id = frappe.db.get_value('Company', doc.company, 'tax_id')
            if not tax_id:
                frappe.throw(
                    _('Tax ID missing for {} in the company document'.format(doc.company)))
            tax_id = f"Seller VAT no: {tax_id}"

            # Time Stamp
            posting_date = getdate(doc.posting_date)
            time = get_time(doc.posting_time)
            seconds = time.hour * 60 * 60 + time.minute * 60 + time.second
            time_stamp = add_to_date(posting_date, seconds=seconds)
            time_stamp = time_stamp.strftime('%Y-%m-%dT%H:%M:%SZ')
            time_stamp = f"Time: {time_stamp}"

            # VAT Amount
            vat_amount = str(doc.total_taxes_and_charges)
            vat_amount = f"Vat Total: {vat_amount}"

            # Invoice Amount
            invoice_amount = str(doc.total)
            invoice_amount = f"Invoice Total: {invoice_amount}"

            # Invoice Customer
            customer = str(doc.customer)
            customer = f"Buyer Name: {customer}"

            # Customer VAT ID
            customer_tax_id = frappe.db.get_value(
                'Customer', doc.customer, 'tax_id')

            qr_string = f"{seller_name}\n{tax_id}\n{time_stamp}\n{vat_amount}\n{invoice_amount}\n{customer}"
            if customer_tax_id:
                customer_tax_id = f"Buyer VAT no: {customer_tax_id}"
                qr_string = f"{qr_string}\n{customer_tax_id}"

            qr_image = io.BytesIO()
            url = qr_create(qr_string, error='L', encoding="utf-8")
            url.png(qr_image, scale=2, quiet_zone=1)

            # making file
            filename = f"QR-CODE-{doc.name}.png".replace(os.path.sep, "__")
            _file = frappe.get_doc({
                "doctype": "File",
                "file_name": filename,
                "content": qr_image.getvalue(),
                "is_private": 0
            })

            _file.save()

            # assigning to document
            doc.db_set('qr_code', _file.file_url)
            doc.notify_update()

            break


def delete_qr_code_file(doc, method):
    """Delete QR Code on deleted sales invoice"""

    region = get_region(doc.company)
    if region not in ['Saudi Arabia']:
        return

    if hasattr(doc, 'qr_code'):
        if doc.get('qr_code'):
            file_doc = frappe.get_list('File', {
                'file_url': doc.qr_code,
                'attached_to_doctype': doc.doctype,
                'attached_to_name': doc.name
            })
            if len(file_doc):
                frappe.delete_doc('File', file_doc[0].name)
