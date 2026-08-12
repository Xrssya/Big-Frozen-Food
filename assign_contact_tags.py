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
        print("=== ASSIGNING CONTACT TAGS / LABELS TO PARTNERS ===")

        # 1. Fetch existing tags created by user (Agen, Reseller, Umum)
        tag_agen = env['res.partner.category'].search([('name', '=', 'Agen')], limit=1)
        tag_reseller = env['res.partner.category'].search([('name', '=', 'Reseller')], limit=1)
        tag_umum = env['res.partner.category'].search([('name', '=', 'Umum')], limit=1)

        # Create 'Vendor' tag if not present
        tag_vendor = env['res.partner.category'].search([('name', 'ilike', 'Vendor')], limit=1)
        if not tag_vendor:
            tag_vendor = env['res.partner.category'].create({'name': 'Vendor / Supplier', 'color': 2})

        print(f" Found Tags - Agen: {tag_agen.id if tag_agen else 'N/A'}, Reseller: {tag_reseller.id if tag_reseller else 'N/A'}, Umum: {tag_umum.id if tag_umum else 'N/A'}, Vendor: {tag_vendor.id}")

        # 2. Tag Agen Customers
        if tag_agen:
            agen_partners = env['res.partner'].search([('name', 'ilike', 'Agen')])
            for p in agen_partners:
                p.write({'category_id': [(4, tag_agen.id)]})
            print(f" Assigned 'Agen' label to {len(agen_partners)} contacts.")

        # 3. Tag Reseller Customers
        if tag_reseller:
            reseller_partners = env['res.partner'].search([('name', 'ilike', 'Reseller')])
            for p in reseller_partners:
                p.write({'category_id': [(4, tag_reseller.id)]})
            print(f" Assigned 'Reseller' label to {len(reseller_partners)} contacts.")

        # 4. Tag Umum Customers
        if tag_umum:
            umum_partners = env['res.partner'].search(['|', ('name', 'ilike', 'Umum'), ('name', '=', 'Pembeli Umum')])
            for p in umum_partners:
                p.write({'category_id': [(4, tag_umum.id)]})
            print(f" Assigned 'Umum' label to {len(umum_partners)} contacts.")

        # 5. Tag Vendor / Suppliers
        vendor_partners = env['res.partner'].search([('supplier_rank', '>', 0)])
        for p in vendor_partners:
            p.write({'category_id': [(4, tag_vendor.id)]})
        print(f" Assigned 'Vendor / Supplier' label to {len(vendor_partners)} contacts.")

        cr.commit()
        print("=== SUCCESS: ALL CONTACT TAGS ASSIGNED CLEANLY ===")

if __name__ == '__main__':
    run()
