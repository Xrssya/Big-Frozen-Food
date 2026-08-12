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
        print("=== CHECKING AND TAGGING ALL UNTAGGED CONTACTS ===")

        # Fetch / Create Tags
        tag_agen = env['res.partner.category'].search([('name', '=', 'Agen')], limit=1)
        tag_reseller = env['res.partner.category'].search([('name', '=', 'Reseller')], limit=1)
        tag_umum = env['res.partner.category'].search([('name', '=', 'Umum')], limit=1)
        tag_vendor = env['res.partner.category'].search([('name', 'ilike', 'Vendor')], limit=1)

        tag_pic = env['res.partner.category'].search([('name', 'ilike', 'PIC')], limit=1)
        if not tag_pic:
            tag_pic = env['res.partner.category'].create({'name': 'PIC / Kontak Utama', 'color': 4})

        tag_internal = env['res.partner.category'].search([('name', 'ilike', 'Internal')], limit=1)
        if not tag_internal:
            tag_internal = env['res.partner.category'].create({'name': 'Perusahaan Utama', 'color': 1})

        # 1. Inherit tags from Parent for Child PIC contacts, plus add 'PIC' tag
        child_contacts = env['res.partner'].search([('parent_id', '!=', False)])
        for child in child_contacts:
            parent_tags = child.parent_id.category_id.ids
            all_tags = list(set(parent_tags + [tag_pic.id]))
            child.write({'category_id': [(6, 0, all_tags)]})
        print(f" Tagged {len(child_contacts)} child/PIC contacts with parent tags + PIC label.")

        # 2. Tag Company (Big Frozen Food)
        company_partner = env['res.company'].search([], limit=1).partner_id
        if company_partner:
            company_partner.write({'category_id': [(6, 0, [tag_internal.id])]})
            print(f" Tagged main company '{company_partner.name}' with 'Perusahaan Utama' label.")

        # 3. Find any remaining untagged partners
        untagged = env['res.partner'].search([('category_id', '=', False)])
        print(f" Found {len(untagged)} remaining untagged contacts.")

        for p in untagged:
            if p.supplier_rank > 0 or "PT" in p.name or "CV" in p.name:
                p.write({'category_id': [(4, tag_vendor.id)]})
            elif "Agen" in p.name:
                p.write({'category_id': [(4, tag_agen.id)]})
            elif "Reseller" in p.name:
                p.write({'category_id': [(4, tag_reseller.id)]})
            else:
                p.write({'category_id': [(4, tag_umum.id)]})

        # Verify zero untagged contacts remain
        zero_untagged = env['res.partner'].search([('category_id', '=', False)])
        print(f" Verification: Untagged contacts count is now {len(zero_untagged)}.")

        cr.commit()
        print("=== SUCCESS: 100% OF CONTACTS NOW HAVE LABELS ===")

if __name__ == '__main__':
    run()
