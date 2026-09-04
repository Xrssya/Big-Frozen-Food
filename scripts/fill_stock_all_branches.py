#!/usr/bin/env python3
"""Isi stok semua produk di semua cabang (lokasi internal per company)."""
import sys
sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'odoo-big-frozen'
CONFIG_PATH = '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf'

LOW_STOCK_KEYWORDS = [
    'Chicken Karaage 500g',
    'French Fries Shoestring 2kg',
    'Saus Sambal Extra Pedas 1kg',
    'Siomay Udang 500g',
    'Scallop Singapore 500g',
]

DEFAULT_QTY = 150.0
LOW_QTY = 8.0
MIN_ALERT_QTY = 10.0

def run():
    odoo.tools.config.parse_config(['-c', CONFIG_PATH, '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print(f"Terhubung ke DB: {DB_NAME}\n")

        companies = env['res.company'].search([])
        print(f"Ditemukan {len(companies)} perusahaan/cabang:")
        for c in companies:
            print(f"  - [{c.id}] {c.name}")

        products = env['product.product'].search([('is_storable', '=', True)])
        print(f"\nDitemukan {len(products)} produk storable.\n")

        total_updated = 0
        total_created = 0

        for company in companies:
            locations = env['stock.location'].search([
                ('usage', '=', 'internal'),
                ('company_id', '=', company.id),
            ])

            if not locations:
                print(f"  {company.name}: tidak ada lokasi internal, skip.")
                continue

            print(f"\n{company.name} ({len(locations)} lokasi internal):")

            for loc in locations:
                for p in products:
                    is_low = any(kw.lower() in p.name.lower() for kw in LOW_STOCK_KEYWORDS)
                    target_qty = LOW_QTY if is_low else DEFAULT_QTY

                    quant = env['stock.quant'].search([
                        ('product_id', '=', p.id),
                        ('location_id', '=', loc.id),
                    ], limit=1)

                    if quant:
                        if quant.quantity < target_qty:
                            quant.inventory_quantity = target_qty
                            quant.action_apply_inventory()
                            total_updated += 1
                    else:
                        env['stock.quant'].create({
                            'product_id': p.id,
                            'location_id': loc.id,
                            'inventory_quantity': target_qty,
                        }).action_apply_inventory()
                        total_created += 1

                print(f"  OK - [{loc.id}] {loc.complete_name}: {len(products)} produk diisi.")

        cr.commit()
        print(f"\n{'='*60}")
        print(f"SELESAI! Stok semua cabang telah diisi.")
        print(f"  Total quant diupdate : {total_updated}")
        print(f"  Total quant dibuat   : {total_created}")
        print(f"{'='*60}")

if __name__ == '__main__':
    run()
