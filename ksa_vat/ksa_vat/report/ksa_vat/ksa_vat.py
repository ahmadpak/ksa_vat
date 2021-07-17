# Copyright (c) 2013, Havenir Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_data, get_rounded_tax_amount
from redis.client import int_or_none

def execute(filters=None):
	columns = columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "title",
			"label": _("Title"),
			"fieldtype": "Data",
			"width": 300
		},
		{
			"fieldname": "amount",
			"label": _("Amount (SAR)"),
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"fieldname": "adjustment_amount",
			"label": _("Adjustment (SAR)"),
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"fieldname": "vat_amount",
			"label": _("VAT Amount (SAR)"),
			"fieldtype": "Currency",
			"width": 150,
		}
	]

def get_data(filters):
	data = []

	# Get tax category and Account
	company = filters.get('company')
	ksa_vat_setting = frappe.get_doc('KSA VAT Setting', company)
	
	# Sales Heading
	append_data(data, 'VAT on Sales', '', '', '')

	grand_total_taxable_amount = 0
	grand_total_taxable_adjustment_amount = 0
	grand_total_tax = 0

	for vat_account in ksa_vat_setting.ksa_vat_sales_accounts:
		total_taxable_amount, total_taxable_adjustment_amount, \
			total_tax = get_tax_data_for_each_vat_account(vat_account, filters, 'Sales Invoice')
		
		# Adding results to data
		append_data(data, vat_account.title, total_taxable_amount, 
			total_taxable_adjustment_amount, total_tax)
		
		grand_total_taxable_amount += total_taxable_amount
		grand_total_taxable_adjustment_amount += total_taxable_adjustment_amount
		grand_total_tax += total_tax

	# Sales Grand Total
	append_data(data, 'Grand Total', grand_total_taxable_amount, 
		grand_total_taxable_adjustment_amount, grand_total_tax )
	
	# Blank Line
	append_data(data, '', '', '', '')

	# Purchase Heading
	append_data(data, 'VAT on Purchases', '', '', '')

	grand_total_taxable_amount = 0
	grand_total_taxable_adjustment_amount = 0
	grand_total_tax = 0

	for vat_account in ksa_vat_setting.ksa_vat_purchase_accounts:
		total_taxable_amount, total_taxable_adjustment_amount, \
			total_tax = get_tax_data_for_each_vat_account(vat_account, filters, 'Purchase Invoice')
		
		# Adding results to data
		append_data(data, vat_account.title, total_taxable_amount, 
			total_taxable_adjustment_amount, total_tax)

		grand_total_taxable_amount += total_taxable_amount
		grand_total_taxable_adjustment_amount += total_taxable_adjustment_amount
		grand_total_tax += total_tax

	# Purchase Grand Total
	append_data(data, 'Grand Total', grand_total_taxable_amount, 
		grand_total_taxable_adjustment_amount, grand_total_tax )

	return data

def get_tax_data_for_each_vat_account(vat_account, filters, doctype):
	'''
	calculates and returns \n
	total_taxable_amount, total_taxable_adjustment_amount, total_tax'''
	from_date = filters.get('from_date')
	to_date = filters.get('to_date')

	invoices = frappe.get_list(doctype, {
		'tax_category': vat_account.tax_category, 
		'docstatus': 1,
		'posting_date': ['between', [from_date, to_date]]
	})

	total_taxable_amount = 0
	total_taxable_adjustment_amount = 0
	total_tax = 0
	for invoice in invoices:
		invoice = frappe.get_doc(doctype, invoice.name)
		
		# Summing up total taxeable amount
		if invoice.is_return == 0:
			total_taxable_amount += get_taxable_amount(invoice.items, vat_account.tax_category)
		
		if invoice.is_return == 1:
			total_taxable_adjustment_amount += get_taxable_amount(invoice.items, vat_account.tax_category)

		# Summing up total tax
		total_tax += get_tax_amount(invoice.taxes, vat_account.account)
	
	return total_taxable_amount, total_taxable_adjustment_amount, total_tax
		


def append_data(data, title, amount, adjustment_amount, vat_amount):
	"""Returns data with appended value."""
	data.append({"title":title, "amount": amount, "adjustment_amount": adjustment_amount, "vat_amount": vat_amount})

def get_taxable_amount(items, tax_category):
	itemised_taxable_amount = 0
	for item in items:
		item_tax = frappe.db.exists({
			'doctype': 'Item Tax',
			'item_tax_template': item.item_tax_template,
			'tax_category': tax_category,
			'parent': item.item_code
		})

		if len(item_tax):
			itemised_taxable_amount += item.net_amount

	return itemised_taxable_amount

def get_tax_amount(taxes, account_head):
	tax_amount = 0
	for tax in taxes:
		if tax.account_head == account_head:
			tax_amount += tax.base_tax_amount

	return tax_amount