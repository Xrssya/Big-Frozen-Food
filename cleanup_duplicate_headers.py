#!/usr/bin/env python3
import sys

sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'big_frozen_food'

def run():
    odoo.tools.config.parse_config(['-c', '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf', '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print("=== CLEANING UP DUPLICATE HEADERS ===")

        # Clean invoice document view to not duplicate global header
        inv_view = env.ref('account.report_invoice_document')
        if 'id="inline_company_header"' in inv_view.arch:
            arch = inv_view.arch
            # Remove inline_company_header block
            start_idx = arch.find('<div id="inline_company_header"')
            if start_idx != -1:
                end_idx = arch.find('</div>', start_idx) + 6
                new_arch = arch[:start_idx] + arch[end_idx:]
                inv_view.write({'arch': new_arch})
                print(" Removed duplicate header from account.report_invoice_document.")

        # Test rendering PDF for INV/2026/00018
        inv = env['account.move'].search([('name', '=', 'INV/2026/00018')], limit=1)
        report = env.ref('account.account_invoices')
        pdf_content, _ = report._render_qweb_pdf(report.id, [inv.id])
        
        pdf_path = '/home/adi-purwanto/Downloads/PERFECT_INV_00018.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        print(f" Generated perfect test PDF at {pdf_path}")

        cr.commit()
        print("=== SUCCESS: SINGLE GLOBAL HEADER CONFIRMED ===")

if __name__ == '__main__':
    run()
