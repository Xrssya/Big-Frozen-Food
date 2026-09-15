#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'odoo-big-frozen'
CONFIG_FILE = '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf'

def upgrade():
    print("=== UPGRADING MODULES TO CREATE DATABASE COLUMNS ===")
    odoo.tools.config.parse_config(['-c', CONFIG_FILE, '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        mods = env['ir.module.module'].search([('name', 'in', ['muk_web_appsbar', 'muk_web_theme', 'bff_stock_control', 'bff_reports', 'bff_pos_receipt'])])
        for m in mods:
            print(f" Marking module '{m.name}' for upgrade...")
            m.button_immediate_upgrade()

        cr.commit()
    print("=== MODULE UPGRADE COMPLETED ===")

if __name__ == '__main__':
    upgrade()
