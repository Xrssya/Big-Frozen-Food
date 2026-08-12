#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'big_frozen_food'

def run():
    odoo.tools.config.parse_config(['-c', '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf', '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print("=== DEBUGGING INVOICE PDF GENERATION ===")

        inv = env['account.move'].search([('name', '=', 'INV/2026/00014')], limit=1)
        assert inv, "Invoice INV/2026/00014 not found!"

        company = inv.company_id
        print(f" Invoice Company: {company.name} (ID: {company.id}) | Logo size: {len(company.logo) if company.logo else 0}")
        print(f" Paperformat ID: {company.paperformat_id.name if company.paperformat_id else 'Default'}")
        print(f" Layout ID: {company.external_report_layout_id.name if company.external_report_layout_id else 'Default'}")

        # Render QWeb HTML first
        report = env.ref('account.account_invoices')
        html_content, report_type = report._render_qweb_html(report.id, [inv.id])
        
        # Save HTML for inspection
        with open('/tmp/test_invoice.html', 'wb') as f:
            f.write(html_content)
        print(" Saved QWeb HTML to /tmp/test_invoice.html")

        # Render QWeb PDF
        pdf_content, _ = report._render_qweb_pdf(report.id, [inv.id])
        pdf_path = '/home/adi-purwanto/Downloads/TEST_INV_00014.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        print(f" Saved rendered PDF directly to {pdf_path}")

if __name__ == '__main__':
    run()
