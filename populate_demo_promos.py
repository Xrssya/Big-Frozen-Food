#!/usr/bin/env python3
import sys
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

        promo_model = env['product.discount.promo']
        count = promo_model.search_count([])
        if count == 0:
            print("Creating demo promo records...")
            cat_nugget = env['product.category'].search([('name', 'ilike', 'Nugget')], limit=1)
            cat_sosis = env['product.category'].search([('name', 'ilike', 'Sosis')], limit=1)

            promos = [
                {
                    'name': 'Promo Kemerdekaan Nugget 10%',
                    'code': 'PROMO-NUGGET10',
                    'discount_type': 'percentage',
                    'discount_value': 10.0,
                    'apply_on': 'category' if cat_nugget else 'all',
                    'category_id': cat_nugget.id if cat_nugget else False,
                    'notes': 'Potongan harga 10% khusus kategori Nugget.'
                },
                {
                    'name': 'Diskon Spesial Sosis Rp 5.000',
                    'code': 'PROMO-SOSIS5K',
                    'discount_type': 'fixed',
                    'discount_value': 5000.0,
                    'apply_on': 'category' if cat_sosis else 'all',
                    'category_id': cat_sosis.id if cat_sosis else False,
                    'notes': 'Potongan Rp 5.000 per produk kategori Sosis.'
                },
                {
                    'name': 'Promo Flash Sale All Items 5%',
                    'code': 'FLASHSALE5',
                    'discount_type': 'percentage',
                    'discount_value': 5.0,
                    'apply_on': 'all',
                    'notes': 'Promo berlaku untuk seluruh item Big Frozen Food.'
                }
            ]

            for p in promos:
                rec = promo_model.create(p)
                print(f"Created Promo: {rec.name} (ID: {rec.id})")
            cr.commit()
            print("Demo promo records created successfully!")
        else:
            print(f"Promo records already exist ({count} records).")

if __name__ == '__main__':
    run()
