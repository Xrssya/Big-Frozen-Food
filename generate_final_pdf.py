#!/usr/bin/env python3
import sys

sys.path.insert(0, '/home/setyo/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'big_frozen_food'

def run():
    odoo.tools.config.parse_config(['-c', '/home/setyo/developer/odoo/odoo-BigFrozenFood/big_frozen_food.conf', '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Test rendering PDF for INV/2026/00014
        inv = env['account.move'].search([('name', '=', 'INV/2026/00014')], limit=1)
        report = env.ref('account.account_invoices')
        pdf_content, _ = report._render_qweb_pdf(report.id, [inv.id])
        
        pdf_path = '/tmp/final_perfect.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        print(f" Generated final perfect test PDF at {pdf_path}")

if __name__ == '__main__':
    run()
