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
        print("=== FIXING HEADER POSITION TO VERY TOP ABOVE FAKTUR TITLE ===")

        # 1. Clean web.external_layout_standard of global_inline_header
        ext_view = env.ref('web.external_layout_standard')
        ext_arch = ext_view.arch
        if 'id="global_inline_header"' in ext_arch:
            s_idx = ext_arch.find('<div id="global_inline_header"')
            if s_idx != -1:
                e_idx = ext_arch.find('</div>', s_idx) + 6
                cleaned_ext_arch = ext_arch[:s_idx] + ext_arch[e_idx:]
                ext_view.with_context(lang='id_ID').write({'arch': cleaned_ext_arch})
                print(" Removed global_inline_header from web.external_layout_standard.")

        # 2. Modify account.report_invoice_document so header is at VERY TOP before partner address & title
        inv_view = env.ref('account.report_invoice_document')
        inv_arch = inv_view.arch

        # Clean any previous inline_company_header
        if 'id="inline_company_header"' in inv_arch:
            s_idx = inv_arch.find('<div id="inline_company_header"')
            if s_idx != -1:
                e_idx = inv_arch.find('</div>', s_idx) + 6
                inv_arch = inv_arch[:s_idx] + inv_arch[e_idx:]

        # Top Company Header HTML
        top_header_html = """
        <div id="inline_company_header" class="row mb-4 pb-2" style="border-bottom: 2px solid #1a5276;">
            <div class="col-6">
                <img t-if="o.company_id.logo" t-att-src="image_data_uri(o.company_id.logo)" style="max-height: 80px;" alt="Logo"/>
                <h3 class="mt-2" style="font-weight: bold; color: #1a5276;"><t t-esc="o.company_id.name"/></h3>
            </div>
            <div class="col-6 text-end" style="font-size: 12px; line-height: 1.4; color: #333;">
                <t t-esc="o.company_id.street"/>, <t t-esc="o.company_id.city"/><br/>
                <span>Telp: </span><t t-esc="o.company_id.phone"/> | <span>Email: </span><t t-esc="o.company_id.email"/><br/>
                <span t-if="o.company_id.vat"><strong>NPWP: </strong><t t-esc="o.company_id.vat"/></span>
            </div>
        </div>
        """

        # Place top_header_html RIGHT AFTER <t t-set="forced_vat"...> (which is before address row and before <h2>)
        target_marker = '<t t-set="forced_vat" t-value="o.fiscal_position_id.foreign_vat"/>'
        if target_marker in inv_arch:
            new_inv_arch = inv_arch.replace(target_marker, target_marker + '\n' + top_header_html)
            inv_view.with_context(lang='id_ID').write({'arch': new_inv_arch})
            print(" Placed company header at VERY TOP of account.report_invoice_document!")

        # Test rendering PDF for INV/2026/00014
        inv = env['account.move'].search([('name', '=', 'INV/2026/00014')], limit=1)
        report = env.ref('account.account_invoices')
        pdf_content, _ = report._render_qweb_pdf(report.id, [inv.id])
        
        pdf_path = '/home/adi-purwanto/Downloads/PERFECT_TOP_HEADER_INV_00014.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        print(f" Generated test PDF at {pdf_path}")

        cr.commit()
        print("=== SUCCESS: HEADER POSITION FIXED TO VERY TOP ===")

if __name__ == '__main__':
    run()
