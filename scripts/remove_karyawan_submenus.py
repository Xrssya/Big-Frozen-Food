#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/setyo/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'bigfrozenfood_db'
CONF_PATH = '/home/setyo/developer/odoo/odoo-BigFrozenFood/big_frozen_food.conf'

def remove_menus():
    odoo.tools.config.parse_config(['-c', CONF_PATH, '-d', DB_NAME, '-u', 'bff_karyawan'])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print("=== REMOVING TIM KASIR & TIM GUDANG MENUS ===")
        menu_cashier = env.ref('bff_karyawan.menu_bff_karyawan_cashier', raise_if_not_found=False)
        if menu_cashier:
            print(f" -> Deleting menu: {menu_cashier.name} (ID: {menu_cashier.id})")
            menu_cashier.unlink()

        menu_wh = env.ref('bff_karyawan.menu_bff_karyawan_warehouse', raise_if_not_found=False)
        if menu_wh:
            print(f" -> Deleting menu: {menu_wh.name} (ID: {menu_wh.id})")
            menu_wh.unlink()

        # Also search by name if ref not found
        extra_menus = env['ir.ui.menu'].search([('name', 'in', ['Tim Kasir', 'Tim Gudang'])])
        for em in extra_menus:
            print(f" -> Deleting menu by name: {em.name} (ID: {em.id})")
            em.unlink()

        cr.commit()
        print(" -> Menus deleted successfully!")

if __name__ == '__main__':
    remove_menus()
