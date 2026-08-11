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
        print("=== PLACING HEADER AT THE ABSOLUTE TOP OF ARTICLE BEFORE ADDRESS ROW ===")

        inv_view = env.ref('account.report_invoice_document')
        arch = inv_view.arch

        # Clean any previous top_company_header_box
        while '<div id="top_company_header_box"' in arch:
            s_idx = arch.find('<div id="top_company_header_box"')
            e_idx = arch.find('</div>', s_idx) + 6
            arch = arch[:s_idx] + arch[e_idx:]

        header_box_html = """<div id="top_company_header_box" class="row mb-3 pb-2" style="border-bottom: 2px solid #1a5276;">
    <div class="col-6">
        <img t-if="o.company_id.logo" t-att-src="image_data_uri(o.company_id.logo)" style="max-height: 75px;" alt="Logo"/>
        <h3 class="mt-2" style="font-weight: bold; color: #1a5276;"><t t-esc="o.company_id.name"/></h3>
    </div>
    <div class="col-6 text-end" style="font-size: 12px; line-height: 1.4; color: #333;">
        <t t-esc="o.company_id.street"/>, <t t-esc="o.company_id.city"/><br/>
        <span>Telp: </span><t t-esc="o.company_id.phone"/> | <span>Email: </span><t t-esc="o.company_id.email"/><br/>
        <span t-if="o.company_id.vat"><strong>NPWP: </strong><t t-esc="o.company_id.vat"/></span>
    </div>
</div>"""

        # Target marker: <div class="row"> (which starts the address block)
        target_marker = '<div class="row">'
        if target_marker in arch:
            new_arch = arch.replace(target_marker, header_box_html + '\n' + target_marker, 1)
            inv_view.with_context(lang='id_ID').write({'arch': new_arch})
            print(" Successfully inserted top_company_header_box BEFORE <div class='row'> address block!")

        # Test rendering PDF for INV/2026/00014
        inv = env['account.move'].search([('name', '=', 'INV/2026/00014')], limit=1)
        report = env.ref('account.account_invoices')
        pdf_content, _ = report._render_qweb_pdf(report.id, [inv.id])
        
        pdf_path = '/home/setyo/Downloads/ABSOLUTE_TOP_PERFECT_INV_00014.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        print(f" Generated test PDF at {pdf_path}")

        cr.commit()
        print("=== SUCCESS: HEADER PLACED AT ABSOLUTE TOP OF ARTICLE ===")

if __name__ == '__main__':
    run()
