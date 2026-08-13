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
        print("=== PLACING INLINE COMPANY HEADER AT VERY TOP BEFORE H2 TITLE ===")

        inv_view = env.ref('account.report_invoice_document')
        arch = inv_view.arch

        # Clean any previous inline_company_header if present
        if 'id="inline_company_header"' in arch:
            s_idx = arch.find('<div id="inline_company_header"')
            if s_idx != -1:
                e_idx = arch.find('</div>', s_idx) + 6
                arch = arch[:s_idx] + arch[e_idx:]

        header_html = """
        <div id="inline_company_header" class="row mb-4 pb-3" style="border-bottom: 2px solid #000;">
            <div class="col-6">
                <img t-if="o.company_id.logo" t-att-src="image_data_uri(o.company_id.logo)" style="max-height: 80px;" alt="Logo"/>
                <h3 class="mt-2" style="font-weight: bold; color: #1a5276;"><t t-esc="o.company_id.name"/></h3>
            </div>
            <div class="col-6 text-end" style="font-size: 13px; line-height: 1.3;">
                <t t-esc="o.company_id.street"/>, <t t-esc="o.company_id.city"/><br/>
                <span>Telp: </span><t t-esc="o.company_id.phone"/> | <span>Email: </span><t t-esc="o.company_id.email"/><br/>
                <span t-if="o.company_id.vat"><strong>NPWP: </strong><t t-esc="o.company_id.vat"/></span>
            </div>
        </div>
        """

        # Target <h2> tag
        target_marker = '<h2>'
        if target_marker in arch:
            new_arch = arch.replace(target_marker, header_html + '\n' + target_marker, 1)
            inv_view.with_context(lang='id_ID').write({'arch': new_arch})
            print(" Placed company header BEFORE <h2> title in account.report_invoice_document view!")

        # Test rendering PDF for INV/2026/00014
        inv = env['account.move'].search([('name', '=', 'INV/2026/00014')], limit=1)
        report = env.ref('account.account_invoices')
        pdf_content, _ = report._render_qweb_pdf(report.id, [inv.id])
        
        pdf_path = '/home/adi-purwanto/Downloads/PERFECT_HEADER_TOP_INV_00014.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        print(f" Generated test PDF at {pdf_path}")

        cr.commit()
        print("=== SUCCESS: HEADER PLACED BEFORE H2 TITLE ===")

if __name__ == '__main__':
    run()
