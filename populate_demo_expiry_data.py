#!/usr/bin/env python3
import sys
from datetime import datetime, timedelta

sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'odoo-big-frozen'
CONFIG_PATH = '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf'

def run():
    odoo.tools.config.parse_config(['-c', CONFIG_PATH, '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print(f"Connected to Odoo 18 for DB: {DB_NAME}")

        today = datetime.now().date()
        target_product_names = [
            "Bakso Ayam 500g",
            "Nugget Coin 500g",
            "Sosis Ayam 500g",
            "Fish Roll 500g"
        ]

        lot_obj = env['stock.lot']
        product_obj = env['product.product']

        for name in target_product_names:
            prod = product_obj.search([('name', '=', name)], limit=1)
            if not prod:
                continue

            # Set product expiry parameters
            prod.product_tmpl_id.write({
                'shelf_life_days': 180,
                'near_expiry_alert_days': 30,
                'auto_clearance_promo': True,
                'clearance_discount_percent': 30.0
            })

            # Create or update lot with expiration date in H-12 days (Near Expiry)
            exp_date = today + timedelta(days=12)
            lot_name = f"LOT-CLR-{prod.id}-{exp_date.strftime('%Y%m%d')}"
            
            existing_lot = lot_obj.search([('name', '=', lot_name), ('product_id', '=', prod.id)], limit=1)
            if not existing_lot:
                lot = lot_obj.create({
                    'name': lot_name,
                    'product_id': prod.id,
                    'expiration_date': exp_date.strftime('%Y-%m-%d 00:00:00')
                })
                print(f"Created Lot {lot.name} for product {prod.name} (Expiry: {exp_date})")
            else:
                existing_lot.write({'expiration_date': exp_date.strftime('%Y-%m-%d 00:00:00')})

        # Sync Clearance Sale promo
        env['product.discount.promo'].sync_near_expiry_clearance_promo()
        cr.commit()
        print("Demo expiry data & Clearance Sale Promo synchronized successfully!")

if __name__ == '__main__':
    run()
