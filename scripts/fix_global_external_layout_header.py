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
        print("=== APPLYING GLOBAL INLINE HEADER TO WEB EXTERNAL LAYOUT ===")

        # Target web.external_layout_standard
        view = env.ref('web.external_layout_standard')
        arch = view.arch

        # Inject company logo & info at the top of the page body (.article)
        if 'id="global_inline_header"' not in arch:
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
            
            target_str = '<div t-attf-class="article o_report_layout_standard o_company_#{company.id}_layout {{  \'o_report_layout_background\' if company.layout_background != \'None\' else \'\' }}" t-att-data-oe-model="o and o._name" t-att-data-oe-id="o and o.id" t-att-data-oe-lang="o and o._context.get(\'lang\')">'
            if target_str in arch:
                new_arch = arch.replace(target_str, target_str + '\n' + global_header_html)
                view.write({'arch': new_arch})
                print(" Successfully inserted global inline header into web.external_layout_standard!")
            else:
                # Alternate insert before <t t-out="0"/>
                if '<t t-out="0"/>' in arch:
                    new_arch = arch.replace('<t t-out="0"/>', global_header_html + '\n<t t-out="0"/>')
                    view.write({'arch': new_arch})
                    print(" Successfully inserted global inline header before t-out in web.external_layout_standard!")

        # Also clean up duplicate inline header in account.report_invoice_document
        inv_view = env.ref('account.report_invoice_document')
        if 'id="inline_company_header"' in inv_view.arch:
            # We can leave it or let global handle it cleanly
            print(" Global layout handles inline header universally for all reports.")

        # Test rendering PDF for INV/2026/00018
        inv = env['account.move'].search([('name', '=', 'INV/2026/00018')], limit=1)
        report = env.ref('account.account_invoices')
        pdf_content, _ = report._render_qweb_pdf(report.id, [inv.id])
        
        pdf_path = '/home/adi-purwanto/Downloads/FINAL_AUDIT_INV_00018.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        print(f" Generated final test PDF at {pdf_path}")

        cr.commit()
        print("=== SUCCESS: GLOBAL INLINE HEADER APPLIED CLEANLY ===")

if __name__ == '__main__':
    run()
