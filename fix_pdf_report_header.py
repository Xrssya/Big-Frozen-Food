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
        print("=== FIXING PDF REPORT HEADER & LOGO RENDERING ===")

        # 1. Set System Parameters for wkhtmltopdf
        env['ir.config_parameter'].sudo().set_param('web.base.url', 'http://127.0.0.1:8069')
        env['ir.config_parameter'].sudo().set_param('report.url', 'http://127.0.0.1:8069')

        # 2. Update Company External Layout to Standard / Boxed for clean PDF
        company = env['res.company'].search([], limit=1)
        
        layout_standard = env.ref('web.external_layout_standard', raise_if_not_found=False)
        layout_bold = env.ref('web.external_layout_bold', raise_if_not_found=False)
        layout_boxed = env.ref('web.external_layout_boxed', raise_if_not_found=False)

        chosen_layout = layout_standard or layout_boxed or layout_bold
        if chosen_layout:
            company.write({
                'external_report_layout_id': chosen_layout.id,
            })
            print(f" Set company report layout to '{chosen_layout.name}'.")

        # 3. Ensure Paper Format top margin is optimal
        paperformats = env['report.paperformat'].search([])
        for pf in paperformats:
            pf.write({
                'margin_top': 40,
                'header_spacing': 35,
            })
        print(f" Adjusted {len(paperformats)} paper formats header margins.")

        cr.commit()
        print("=== SUCCESS: PDF REPORT HEADER & LOGO CONFIGURATION FIXED ===")

if __name__ == '__main__':
    run()
