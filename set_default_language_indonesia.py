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
        print("=== SETTING DEFAULT LANGUAGE TO INDONESIAN (id_ID) ===")

        # 1. Activate Indonesian Language (id_ID)
        lang_id = env['res.lang'].with_context(active_test=False).search([('code', '=', 'id_ID')], limit=1)
        if lang_id:
            lang_id.write({'active': True})
            print(" Indonesian language (id_ID) activated in res.lang.")
        else:
            # Install language if not present
            lang_installer = env['base.language.install'].create({'lang_ids': [(6, 0, [lang_id.id])]})
            lang_installer.lang_install()
            print(" Installed Indonesian language.")

        # Try installing translations if needed
        try:
            env['base.language.install'].create({
                'overwrite': True,
            }).lang_install()
        except Exception as e:
            print(" Note on lang install:", e)

        # 2. Update all Users' language to id_ID
        users = env['res.users'].search([])
        users.write({'lang': 'id_ID'})
        print(f" Updated language for {len(users)} users to Indonesian (id_ID).")

        # 3. Update all Partners' (Contacts) language to id_ID
        partners = env['res.partner'].search([])
        partners.write({'lang': 'id_ID'})
        print(f" Updated language for {len(partners)} contacts to Indonesian (id_ID).")

        # 4. Set Default value for new Partners to id_ID via ir.default or field default
        env['ir.default'].set('res.partner', 'lang', 'id_ID')
        print(" Set default language for NEW contacts to Indonesian (id_ID).")

        cr.commit()
        print("=== SUCCESS: DEFAULT LANGUAGE IS NOW INDONESIAN (id_ID) ===")

if __name__ == '__main__':
    run()
