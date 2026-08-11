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
        print("=== RENDERING CLEAN PDF FOR INV/2026/00018 ===")

        # Inject global header into web.external_layout_standard cleanly
        ext_view = env.ref('web.external_layout_standard')
        ext_arch = ext_view.arch

        if 'id="global_inline_header"' not in ext_arch:
            global_header_html = """
            <div id="global_inline_header" class="row mb-4 pb-3" style="border-bottom: 2px solid #000;">
                <div class="col-6">
                    <img t-if="company.logo" t-att-src="image_data_uri(company.logo)" style="max-height: 85px;" alt="Logo"/>
                    <h3 class="mt-2" style="font-weight: bold; color: #1a5276;"><t t-esc="company.name"/></h3>
                </div>
                <div class="col-6 text-end" style="font-size: 13px; line-height: 1.3;">
                    <t t-esc="company.street"/>, <t t-esc="company.city"/><br/>
                    <span>Telp: </span><t t-esc="company.phone"/> | <span>Email: </span><t t-esc="company.email"/><br/>
                    <span t-if="company.vat"><strong>NPWP: </strong><t t-esc="company.vat"/></span>
                </div>
            </div>
            """
            if '<t t-out="0"/>' in ext_arch:
                new_arch = ext_arch.replace('<t t-out="0"/>', global_header_html + '\n<t t-out="0"/>')
                ext_view.with_context(lang='id_ID').write({'arch': new_arch})
                print(" Injected global header into web.external_layout_standard.")

        # Test rendering PDF for INV/2026/00018
        inv = env['account.move'].search([('name', '=', 'INV/2026/00018')], limit=1)
        report = env.ref('account.account_invoices')
        pdf_content, _ = report._render_qweb_pdf(report.id, [inv.id])
        
        pdf_path = '/home/setyo/Downloads/VERIFIED_INV_00018.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        print(f" Generated verified test PDF at {pdf_path}")

        cr.commit()
        print("=== SUCCESS: CLEAN VERIFIED PDF GENERATED ===")

if __name__ == '__main__':
    run()
