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
        print("=== INJECTING INLINE HEADER AT TOP OF WEB EXTERNAL LAYOUT ===")

        # 1. Upgrade account module to restore original report_invoice_document 100% untouched
        mod = env['ir.module.module'].search([('name', '=', 'account')], limit=1)
        mod.button_immediate_upgrade()
        cr.commit()
        print(" Reloaded account module cleanly.")

        # 2. Modify web.external_layout_standard
        ext_view = env.ref('web.external_layout_standard')
        ext_arch = ext_view.arch

        # Clean any old global_inline_header if present
        while '<div id="global_inline_header"' in ext_arch:
            s_idx = ext_arch.find('<div id="global_inline_header"')
            e_idx = ext_arch.find('</div>', s_idx) + 6
            ext_arch = ext_arch[:s_idx] + ext_arch[e_idx:]

        header_top_html = """<div id="global_inline_header" class="row mb-3 pb-2" style="border-bottom: 2px solid #1a5276;">
    <div class="col-6">
        <img t-if="company.logo" t-att-src="image_data_uri(company.logo)" style="max-height: 80px;" alt="Logo"/>
        <h3 class="mt-2" style="font-weight: bold; color: #1a5276;"><t t-esc="company.name"/></h3>
    </div>
    <div class="col-6 text-end" style="font-size: 12px; line-height: 1.4; color: #333;">
        <t t-esc="company.street"/>, <t t-esc="company.city"/><br/>
        <span>Telp: </span><t t-esc="company.phone"/> | <span>Email: </span><t t-esc="company.email"/><br/>
        <span t-if="company.vat"><strong>NPWP: </strong><t t-esc="company.vat"/></span>
    </div>
</div>"""

        if '<t t-out="address"/>' in ext_arch:
            new_ext_arch = ext_arch.replace('<t t-out="address"/>', header_top_html + '\n<t t-out="address"/>')
            ext_view.with_context(lang='id_ID').write({'arch': new_ext_arch})
            print(" Injected global header before <t t-out='address'/> in web.external_layout_standard!")

        # Test rendering PDF for INV/2026/00014
        inv = env['account.move'].search([('name', '=', 'INV/2026/00014')], limit=1)
        report = env.ref('account.account_invoices')
        pdf_content, _ = report._render_qweb_pdf(report.id, [inv.id])
        
        pdf_path = '/home/setyo/Downloads/PERFECT_WEB_LAYOUT_INV_00014.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        print(f" Generated test PDF at {pdf_path}")

        cr.commit()
        print("=== SUCCESS: INLINE HEADER INJECTED AT TOP OF WEB LAYOUT ===")

if __name__ == '__main__':
    run()
