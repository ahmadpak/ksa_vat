import frappe
import os
import json
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def create_ksa_vat_setting(self, method):
    """
    On creation of first company. Creates KSA VAT Setting"""
    # Validating if this is the first company for Saudi Arab
    company_list = frappe.get_all('Company', {
        'country': 'Saudi Arabia'
    })

    ksa_vat_setting = frappe.get_all('KSA VAT Setting', {
        'company': self.name
    })

    if len(company_list) == 1 and len(ksa_vat_setting) == 0:
        make_custom_fields()
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ksa_vat_settings.json')
        with open(file_path, 'r') as json_file:
            account_data = json.load(json_file)
        

        # Creating KSA VAT Setting
        ksa_vat_setting = frappe.get_doc({
            'doctype': 'KSA VAT Setting',
            'company': self.name
        })
        
        for data in account_data:
            if data['type'] == 'Sales Account':
                for row in data['accounts']:
                    item_tax_template = row['item_tax_template']
                    account = row['account']
                    ksa_vat_setting.append('ksa_vat_sales_accounts', {
                        'title': row['title'],
                        'item_tax_template': f'{item_tax_template} - {self.abbr}',
                        'account': f'{account} - {self.abbr}'
                    })
                
            elif data['type'] == 'Purchase Account':
                for row in data['accounts']:
                    item_tax_template = row['item_tax_template']
                    account = row['account']
                    ksa_vat_setting.append('ksa_vat_purchase_accounts', {
                        'title': row['title'],
                        'item_tax_template': f'{item_tax_template} - {self.abbr}',
                        'account': f'{account} - {self.abbr}'
                    })

        ksa_vat_setting.save()

def make_custom_fields():
    qr_code_field = dict(
        fieldname='qr_code', 
        label='QR Code', 
        fieldtype='Attach Image', 
        read_only=1, no_copy=1, hidden=1)
    
    create_custom_field('Sales Invoice', qr_code_field)
