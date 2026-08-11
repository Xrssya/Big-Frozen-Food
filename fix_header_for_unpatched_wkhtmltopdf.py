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
        print("=== INJECTING INLINE COMPANY HEADER FOR UNPATCHED WKHTMLTOPDF ===")

        # Find account.report_invoice_document view
        view = env.ref('account.report_invoice_document')
        arch = view.arch

        # Check if inline header is already added
        if 'id="inline_company_header"' not in arch:
            # Prepare inline header HTML block to insert right after <t t-set="forced_vat"...>
            inline_header_html = """
                <div id="inline_company_header" class="row mb-4 pb-3" style="border-bottom: 2px solid #000;">
                    <div class="col-6">
                        <img t-if="o.company_id.logo" t-att-src="image_data_uri(o.company_id.logo)" style="max-height: 80px;" alt="Logo"/>
                        <h3 class="mt-2" style="font-weight: bold; color: #1a5276;"><t t-esc="o.company_id.name"/></h3>
                        <div style="font-size: 13px; line-height: 1.3;">
                            <t t-esc="o.company_id.street"/>, <t t-esc="o.company_id.city"/><br/>
                            <span>Telp: </span><t t-esc="o.company_id.phone"/> | <span>Email: </span><t t-esc="o.company_id.email"/><br/>
                            <span t-if="o.company_id.vat"><strong>NPWP: </strong><t t-esc="o.company_id.vat"/></span>
                        </div>
                    </div>
                </div>
            """
            
            target_str = '<t t-set="forced_vat" t-value="o.fiscal_position_id.foreign_vat"/>'
            if target_str in arch:
                new_arch = arch.replace(target_str, target_str + '\n' + inline_header_html)
                view.write({'arch': new_arch})
                print(" Successfully inserted inline company header into account.report_invoice_document view.")

        # Test rendering PDF again
        inv = env['account.move'].search([('name', '=', 'INV/2026/00014')], limit=1)
        report = env.ref('account.account_invoices')
        pdf_content, _ = report._render_qweb_pdf(report.id, [inv.id])
        
        pdf_path = '/home/setyo/Downloads/TEST_INV_FIXED_00014.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        print(f" Generated test PDF at {pdf_path}")

        cr.commit()
        print("=== SUCCESS: INLINE COMPANY HEADER INJECTED AND COMMITTED ===")

if __name__ == '__main__':
    run()
