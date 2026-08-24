#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/setyo/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'bigfrozenfood_db'
CONF_PATH = '/home/setyo/developer/odoo/odoo-BigFrozenFood/big_frozen_food.conf'

def configure_sidebar():
    odoo.tools.config.parse_config(['-c', CONF_PATH, '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=========================================================")
        print(" CONFIGURING SPREADSHEET DASHBOARD SIDEBAR (BIG FROZEN FOOD)")
        print("=========================================================")

        Group = env['spreadsheet.dashboard.group']
        Dashboard = env['spreadsheet.dashboard']

        # 1. Prepare Target Groups: Penjualan, Pembelian, Penagihan, Stok
        targets = [
            {'name': 'Penjualan', 'sequence': 10, 'key': 'sales'},
            {'name': 'Pembelian', 'sequence': 20, 'key': 'purchase'},
            {'name': 'Penagihan', 'sequence': 30, 'key': 'finance'},
            {'name': 'Stok', 'sequence': 40, 'key': 'stock'},
        ]

        group_map = {}
        for t in targets:
            g = Group.search([('name', '=', t['name'])], limit=1)
            if not g:
                # Check by English default fallback names if any
                if t['key'] == 'sales':
                    g = Group.search([('name', 'in', ['Sales', 'Penjualan'])], limit=1)
                elif t['key'] == 'finance':
                    g = Group.search([('name', 'in', ['Finance', 'Keuangan', 'Penagihan'])], limit=1)
                elif t['key'] == 'stock':
                    g = Group.search([('name', 'in', ['Logistics', 'Inventory', 'Stock', 'Stok'])], limit=1)

            if g:
                g.write({'name': t['name'], 'sequence': t['sequence']})
            else:
                g = Group.create({'name': t['name'], 'sequence': t['sequence']})
            
            group_map[t['key']] = g
            print(f" -> Group '{g.name}' ready with ID: {g.id} (Seq: {g.sequence})")

        # 2. Assign Dashboards to Groups
        # Penjualan: Dashboard ID 3 (Sales)
        d_sales = Dashboard.browse(3)
        if d_sales.exists():
            d_sales.write({
                'name': 'Penjualan',
                'dashboard_group_id': group_map['sales'].id,
                'sequence': 10
            })
            print(" -> Dashboard 'Penjualan' assigned to Group Penjualan")

        # Hide Product dashboard from main sidebar or move to Penjualan as sub-item
        d_product = Dashboard.browse(4)
        if d_product.exists():
            # If user only wants Penjualan, Pembelian, Penagihan, Stok as main items, we can unpublish or un-group product, or keep it under Penjualan
            d_product.write({'is_published': False})
            print(" -> Dashboard 'Product' unpublished")

        # Penagihan: Dashboard ID 1 (Invoicing)
        d_invoicing = Dashboard.browse(1)
        if d_invoicing.exists():
            d_invoicing.write({
                'name': 'Penagihan',
                'dashboard_group_id': group_map['finance'].id,
                'sequence': 10
            })
            print(" -> Dashboard 'Penagihan' assigned to Group Penagihan")

        # Stok: Dashboard ID 2 (Warehouse Metrics)
        d_stock = Dashboard.browse(2)
        if d_stock.exists():
            d_stock.write({
                'name': 'Stok',
                'dashboard_group_id': group_map['stock'].id,
                'sequence': 10
            })
            print(" -> Dashboard 'Stok' assigned to Group Stok")

        # Pembelian: Check if Purchase Dashboard exists, else duplicate/create one
        d_purchase = Dashboard.search([('name', 'ilike', 'Pembelian')], limit=1)
        if not d_purchase and d_sales.exists():
            # Create a dedicated Purchase dashboard record based on template or copy
            d_purchase = d_sales.copy({
                'name': 'Pembelian',
                'dashboard_group_id': group_map['purchase'].id,
                'sequence': 10,
                'is_published': True
            })
            print(" -> Created Dashboard 'Pembelian' under Group Pembelian")
        elif d_purchase:
            d_purchase.write({
                'name': 'Pembelian',
                'dashboard_group_id': group_map['purchase'].id,
                'sequence': 10,
                'is_published': True
            })
            print(" -> Updated Dashboard 'Pembelian' under Group Pembelian")

        # 3. Clean up sequence for other default groups
        other_groups = Group.search([('id', 'not in', [g.id for g in group_map.values()])])
        for og in other_groups:
            og.write({'sequence': 999})
            print(f" -> Set unused group '{og.name}' sequence to 999")

        cr.commit()
        print("=========================================================")
        print(" SUCCESS! SIDEBAR CUSTOMIZATION COMPLETED.")
        print("=========================================================")

if __name__ == '__main__':
    configure_sidebar()
