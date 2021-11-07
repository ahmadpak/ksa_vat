import frappe
from frappe import _
from erpnext import get_region
from pyqrcode import create as qr_create
import io
import os
import json

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
			# Creating public url to print format
			default_print_format = frappe.db.get_value('Property Setter', dict(property='default_print_format', doc_type=doc.doctype), "value")
			
			# System Language
			language = frappe.get_system_settings('language')
			
			# creating qr code for the url
			url = f"{ frappe.utils.get_url() }/{ doc.doctype }/{ doc.name }?format={ default_print_format or 'Standard' }&_lang={ language }&key={ doc.get_signature() }"
			url = url.replace(" ", "%20")
			
			
			#qr text
			qr_text = '''
Vendor Name / المورد
{0}
____________________________
VAT ID / الرقم الضريبي
{1}
____________________________			
Date & Time / التاريخ الوقت
{2} : {3}
____________________________			
Total VAT Amount / اجمالي الضريبة
{4}
____________________________			
Total Amount / مجموع الاجمالي
{5} 
____________________________
URL / الرابط
{6}
			'''.format(doc.company, doc.tax_id, doc.posting_date, doc.posting_time,
                            doc.base_total_taxes_and_charges, doc.grand_total, url)

			qr_image = io.BytesIO()
			url = qr_create(qr_text, error='L', encoding='utf-8')
			url.png(qr_image, scale=2, quiet_zone=1)
			
			# making file
			filename = f"QR-CODE-{doc.name}.png".replace(os.path.sep, "__")
			_file = frappe.get_doc({
				"doctype": "File",
				"file_name": filename,
				"content": qr_image.getvalue(),
				"is_private": 1
			})

			_file.save()

			# assigning to document
			doc.db_set('qr_code', _file.file_url)
			doc.notify_update()

			break

		else:
			pass

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
