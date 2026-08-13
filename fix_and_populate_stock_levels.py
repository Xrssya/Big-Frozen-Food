#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/rsya/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'odoo-big-frozen'
CONFIG_PATH = '/home/rsya/developer/odoo/Big-Frozen-Food/big_frozen_food.conf'

def run():
    odoo.tools.config.parse_config(['-c', CONFIG_PATH, '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print(f"Connected to Odoo 18 for DB: {DB_NAME}")

        # 1. Get Stock Warehouse & Internal Location
        location = env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        if not location:
            print("Error: No internal stock location found!")
            return

        # 2. Find all storable products (is_storable = True in Odoo 18)
        products = env['product.product'].search([('is_storable', '=', True)])
        print(f"Found {len(products)} storable products.")

        # Products to set specifically as "Low Stock" for demonstration
        low_stock_target_names = [
            "Chicken Karaage 500g",
            "French Fries Shoestring 2kg",
            "Saus Sambal Extra Pedas 1kg",
            "Siomay Udang 500g",
            "Scallop Singapore 500g"
        ]

        for p in products:
            # Set default min stock alert qty to 10
            if not p.min_stock_alert_qty:
                p.min_stock_alert_qty = 10.0

            # Determine target quantity
            is_low_target = any(target.lower() in p.name.lower() for target in low_stock_target_names)
            target_qty = 5.0 if is_low_target else 120.0

            # Update stock quant
            quant = env['stock.quant'].search([('product_id', '=', p.id), ('location_id', '=', location.id)], limit=1)
            if quant:
                quant.inventory_quantity = target_qty
                quant.action_apply_inventory()
            else:
                env['stock.quant'].create({
                    'product_id': p.id,
                    'location_id': location.id,
                    'inventory_quantity': target_qty,
                }).action_apply_inventory()

            status_str = "LOW STOCK (ALERT)" if is_low_target else "OK"
            print(f"• {p.name}: Set Stock = {target_qty} (Min Limit: {p.min_stock_alert_qty}) -> [{status_str}]")

        cr.commit()
        print("\nAll negative stock fixed and low stock demo data applied successfully!")

if __name__ == '__main__':
    run()
