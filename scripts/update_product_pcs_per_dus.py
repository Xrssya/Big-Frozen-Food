#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'odoo-big-frozen'
CONFIG_FILE = '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf'

def run():
    print("=== UPDATING PRODUCT PCS PER DUS & RE-APPLYING INVOICE TEMPLATE ===")
    odoo.tools.config.parse_config(['-c', CONFIG_FILE, '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # 1. Update pcs_per_dus based on category or product size
        products = env['product.template'].search([])
        updated_count = 0
        for p in products:
            name_lower = p.name.lower()
            if '250g' in name_lower or 'dimsum' in name_lower or 'siomay' in name_lower:
                p.pcs_per_dus = 20
            elif '1kg' in name_lower or 'bakso' in name_lower:
                p.pcs_per_dus = 10
            elif '500g' in name_lower or 'nugget' in name_lower or 'sosis' in name_lower:
                p.pcs_per_dus = 12
            else:
                p.pcs_per_dus = 10
            updated_count += 1

        print(f" Updated {updated_count} products with packaging units (pcs_per_dus).")

        # 2. Test format_qty_dus_pack calculation on sample products
        sample_prod = env['product.product'].search([], limit=3)
        for sp in sample_prod:
            print(f" Sample product: '{sp.name}' (1 Dus = {sp.pcs_per_dus} Pack)")
            print(f"   Qty 25 -> {sp.format_qty_dus_pack(25)}")
            print(f"   Qty 20 -> {sp.format_qty_dus_pack(20)}")
            print(f"   Qty 5  -> {sp.format_qty_dus_pack(5)}")

        cr.commit()
        print("=== PRODUCT PCS PER DUS UPDATED SUCCESSFULLY ===")

if __name__ == '__main__':
    run()
