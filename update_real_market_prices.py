#!/usr/bin/env python3
import sys

sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'odoo-big-frozen'

REAL_MARKET_PRICES = {
    # Olahan Daging Sapi & Bakso
    "Bakso Sapi Super 500g": {"price": 54500, "cost": 42000},
    "Bakso Sapi Halus 500g": {"price": 41400, "cost": 31500},
    "Bakso Urat 500g": {"price": 47500, "cost": 36000},
    "Bakso Ayam 500g": {"price": 26500, "cost": 19000},
    "Daging Slice Shortplate 500g": {"price": 68500, "cost": 52000},

    # Nugget
    "Nugget Ayam Original 500g": {"price": 48500, "cost": 37000},
    "Nugget Ayam Crispy 500g": {"price": 53500, "cost": 41000},
    "Nugget Coin 500g": {"price": 32500, "cost": 24000},
    "Nugget Stick 500g": {"price": 34500, "cost": 25500},
    "Nugget Premium 500g": {"price": 56000, "cost": 43000},
    "Nugget Cheese 500g": {"price": 49500, "cost": 38000},

    # Sosis
    "Sosis Ayam 500g": {"price": 25500, "cost": 18500},
    "Sosis Sapi 500g": {"price": 39500, "cost": 29500},
    "Sosis Jumbo 500g": {"price": 54000, "cost": 41500},
    "Sosis Cocktail 500g": {"price": 37500, "cost": 28000},
    "Sosis Bratwurst 500g": {"price": 58500, "cost": 44500},
    "Sosis Cheesy 500g": {"price": 52500, "cost": 40000},

    # Seafood & Olahan Ikan
    "Fish Roll 500g": {"price": 32500, "cost": 24000},
    "Crab Stick 500g": {"price": 31000, "cost": 23000},
    "Fish Dumpling Cheese 500g": {"price": 37500, "cost": 28500},
    "Seafood Ball 500g": {"price": 33500, "cost": 25000},
    "Ebi Furai 500g": {"price": 58000, "cost": 44000},
    "Fish Cake 500g": {"price": 32000, "cost": 24000},
    "Otak-Otak Ikan 500g": {"price": 29500, "cost": 21500},
    "Scallop Singapore 500g": {"price": 31500, "cost": 23000},

    # Dimsum Beku
    "Siomay Ayam 500g": {"price": 36500, "cost": 27000},
    "Siomay Udang 500g": {"price": 45000, "cost": 34000},
    "Hakau Udang 500g": {"price": 48500, "cost": 36500},
    "Gyoza Ayam 500g": {"price": 42500, "cost": 32000},
    "Dimsum Mix 500g": {"price": 41000, "cost": 30500},

    # Kentang Beku & Snack
    "French Fries Shoestring 1kg": {"price": 39500, "cost": 29500},
    "French Fries Crinkle 1kg": {"price": 40500, "cost": 30500},
    "French Fries Shoestring 2kg": {"price": 74500, "cost": 56000},
    "Potato Wedges 1kg": {"price": 46500, "cost": 35000},
    "Hashbrown 1kg": {"price": 48000, "cost": 36000},

    # Ayam & Olahan Unggas
    "Chicken Wings Original 500g": {"price": 57500, "cost": 43500},
    "Chicken Karaage 500g": {"price": 54000, "cost": 41000},
    "Chicken Popcorn 500g": {"price": 43500, "cost": 32500},
    "Chicken Strip 500g": {"price": 46000, "cost": 34500},
    "Chicken Katsu 500g": {"price": 52000, "cost": 39000},

    # Tempura & Olahan Seafood
    "Tempura Udang 500g": {"price": 38500, "cost": 28500},
    "Shrimp Roll 500g": {"price": 43000, "cost": 32000},

    # Bumbu & Pelengkap
    "Saus Tomat 1kg": {"price": 19500, "cost": 14500},
    "Saus Sambal Extra Pedas 1kg": {"price": 23500, "cost": 17500},
    "Mayonaise Original 1kg": {"price": 28500, "cost": 21000},
    "Saus Keju 500g": {"price": 27000, "cost": 19500},
    "Bumbu Tabur Balado 250g": {"price": 16500, "cost": 11500},
}

def run():
    odoo.tools.config.parse_config(['-c', '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf', '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print("=== UPDATING REAL MARKET PRICES FOR BIG FROZEN FOOD ===")
        
        updated_count = 0
        for name, data in REAL_MARKET_PRICES.items():
            product = env['product.product'].search([('name', '=', name)], limit=1)
            if product:
                product.write({
                    'lst_price': data['price'],
                    'standard_price': data['cost'],
                })
                # Also update template
                product.product_tmpl_id.write({
                    'list_price': data['price'],
                    'standard_price': data['cost'],
                })
                updated_count += 1
                print(f" [UPDATED] {name}: Selling Price = Rp {data['price']:,.0f} | Cost = Rp {data['cost']:,.0f}")
            else:
                print(f" [WARNING] Product not found: {name}")

        cr.commit()
        print(f"\nSuccessfully updated {updated_count} products with real market prices.")

if __name__ == '__main__':
    run()
