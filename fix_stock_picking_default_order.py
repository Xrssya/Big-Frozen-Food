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
        print("=== FIXING DEFAULT ORDER FOR STOCK PICKING LIST VIEW ===")

        # Update stock.vpicktree view to set default_order="name desc"
        vpicktree = env.ref('stock.vpicktree')
        arch = vpicktree.arch
        
        if 'default_order=' not in arch:
            new_arch = arch.replace('<list string="Picking list"', '<list string="Picking list" default_order="name desc"', 1)
            vpicktree.write({'arch': new_arch})
            print(" Updated stock.vpicktree with default_order='name desc'!")

        # Also update purchase.order default_order if needed
        po_view = env.ref('purchase.purchase_order_kpis_tree', raise_if_not_found=False) or env.ref('purchase.purchase_order_view_tree', raise_if_not_found=False)
        if po_view and 'default_order=' not in po_view.arch:
            new_arch = po_view.arch.replace('<list string="Purchase Orders"', '<list string="Purchase Orders" default_order="name desc"', 1)
            po_view.write({'arch': new_arch})
            print(" Updated purchase order tree view with default_order='name desc'!")

        # Also update sale.order default order if needed
        so_view = env.ref('sale.sale_order_tree', raise_if_not_found=False) or env.ref('sale.view_order_tree', raise_if_not_found=False)
        if so_view and 'default_order=' not in so_view.arch:
            new_arch = so_view.arch.replace('<list string="Sales Orders"', '<list string="Sales Orders" default_order="name desc"', 1)
            so_view.write({'arch': new_arch})
            print(" Updated sale order tree view with default_order='name desc'!")

        cr.commit()
        print("=== SUCCESS: DEFAULT ORDER SET TO NEWEST FIRST (DESCENDING) ===")

if __name__ == '__main__':
    run()
