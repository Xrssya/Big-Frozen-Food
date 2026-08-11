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
        print("=== DIAGNOSING & FIXING WKHTMLTOPDF HEADER RENDERING ===")

        # Check report action for invoice
        invoice = env['account.move'].search([('name', '=', 'INV/2026/00014')], limit=1)
        assert invoice, "Invoice INV/2026/00014 not found!"

        # Let's inspect paperformat
        paperformat = invoice.company_id.paperformat_id or env.ref('base.paperformat_us')
        print(f" Paperformat used: {paperformat.name} | margin_top={paperformat.margin_top} | header_spacing={paperformat.header_spacing}")

        # Set system parameters so wkhtmltopdf can fetch images over HTTP/loopback
        env['ir.config_parameter'].sudo().set_param('web.base.url', 'http://localhost:8069')
        env['ir.config_parameter'].sudo().set_param('web.base.url.freeze', 'True')
        env['ir.config_parameter'].sudo().set_param('report.url', 'http://127.0.0.1:8069')

        # Also let's check report_header on company
        company = invoice.company_id
        print(f" Company Logo present: {bool(company.logo)} | Company Name: {company.name} | Partner: {company.partner_id.name}")

        # Update paperformat margin_top and header_spacing to 60/50 so header html has enough space!
        paperformat.write({
            'margin_top': 60,
            'header_spacing': 50,
        })
        print(" Updated paperformat margin_top=60, header_spacing=50.")

        # Let's also check if external_layout_standard template renders company logo
        # In Odoo 18, let's update company's report_header text or ensure external layout includes company logo & address
        company.write({
            'report_header': 'BIG FROZEN FOOD - Cold Storage & Distributor Pasuruan',
        })

        cr.commit()
        print("=== RENDER TEST ===")
        # Test rendering PDF via Odoo report engine
        report_action = env.ref('account.account_invoices')
        pdf_content, _ = report_action._render_qweb_pdf([invoice.id])
        with open('/tmp/test_invoice.pdf', 'wb') as f:
            f.write(pdf_content)
        print(" PDF written to /tmp/test_invoice.pdf. Length:", len(pdf_content))

if __name__ == '__main__':
    run()
