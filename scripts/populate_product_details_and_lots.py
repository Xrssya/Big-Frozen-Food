#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'big_frozen_food'

DEFAULT_CODE_MAP = {
    'Bakso Ayam 500g': 'BKS-AYM-500',
    'Bakso Sapi Super 500g': 'BKS-SP-500',
    'Bakso Sapi Halus 500g': 'BKS-HL-500',
    'Bakso Urat 500g': 'BKS-URT-500',
    'Fish Roll 500g': 'FSH-RL-500',
    'Nugget Coin 500g': 'NGT-CN-500',
    'Sosis Ayam 500g': 'SSS-AYM-500',
    'Bumbu Tabur Balado 250g': 'BMB-BAL-250',
    'Chicken Karaage 500g': 'CHK-KRG-500',
}

DESC_IN = "Simpan segera di Cold Storage / Freezer (-18°C). Pindai & catat nomor lot/expired date saat barang masuk."
DESC_OUT = "Pastikan pengiriman menggunakan Cool Box / Thermal Bag. Cek tanggal expired (FEFO) dan kondisi kemasan sebelum diserahkan ke kurir/pelanggan."

def generate_default_code(name):
    words = name.split()
    code_parts = [w[:3].upper() for w in words if w[0].isalnum()]
    return "-".join(code_parts[:3])

def run():
    odoo.tools.config.parse_config(['-c', '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf', '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print(f" Connected to Odoo database: {DB_NAME}")

        # 1. Update Product Templates & Variants
        templates = env['product.template'].search([])
        print(f"\n--- Updating {len(templates)} Product Templates ---")
        
        for tmpl in templates:
            vals = {}
            # Auto-assign Kode Barang / SKU if missing
            if not tmpl.default_code:
                code = DEFAULT_CODE_MAP.get(tmpl.name) or generate_default_code(tmpl.name)
                vals['default_code'] = code
                print(f"  [SKU] Set '{tmpl.name}' -> SKU: {code}")
            
            # Auto-assign Receipt & Delivery picking descriptions if missing
            if not tmpl.description_pickingin:
                vals['description_pickingin'] = DESC_IN
            if not tmpl.description_pickingout:
                vals['description_pickingout'] = DESC_OUT

            if vals:
                tmpl.write(vals)

            # Sync variant default_code
            for variant in tmpl.product_variant_ids:
                if not variant.default_code:
                    variant.write({'default_code': tmpl.default_code})

            # Populate Packaging Table if empty
            if not tmpl.packaging_ids:
                variant = tmpl.product_variant_ids[:1]
                if variant:
                    pcs_dus_val = getattr(tmpl, 'pcs_per_dus', False) or getattr(tmpl, 'pcs_per_box', False) or 10
                    pcs_dus = float(pcs_dus_val or 10)
                    env['product.packaging'].create([
                        {
                            'name': 'Dus / Kardus',
                            'qty': pcs_dus,
                            'sales': True,
                            'purchase': True,
                            'product_id': variant.id,
                        },
                        {
                            'name': 'Slop / Bal',
                            'qty': 5.0,
                            'sales': True,
                            'purchase': False,
                            'product_id': variant.id,
                        }
                    ])
                    print(f"  [Packaging] Added default multi-kemasan for '{tmpl.name}' (Dus {int(pcs_dus)} Pack, Slop 5 Pack)")

        # 2. Update Stock Lots
        lots = env['stock.lot'].search([])
        print(f"\n--- Updating {len(lots)} Stock Lots ---")

        for lot in lots:
            product = lot.product_id
            sku = product.default_code or (product.product_tmpl_id and product.product_tmpl_id.default_code) or ""
            
            lot_vals = {}
            # Set Referensi Internal on lot if empty
            if not lot.ref and sku:
                lot_vals['ref'] = sku
                print(f"  [Lot Ref] Set Lot '{lot.name}' -> Ref Internal: {sku}")

            # Enhance Lot Name if generic like LOT-15-20260821 or LOT-2026-EXP001
            if sku and ("LOT-" in lot.name and ("-" in lot.name)):
                parts = lot.name.split("-")
                # If middle part is pure digits (e.g. LOT-15-20260821)
                if len(parts) >= 3 and parts[1].isdigit():
                    new_name = f"LOT-{sku.replace('-', '')}-{parts[2]}"
                    lot_vals['name'] = new_name
                    print(f"  [Lot Name] Rename '{lot.name}' -> '{new_name}'")

            if lot_vals:
                lot.write(lot_vals)

        cr.commit()
        print("\n ALL PRODUCT DETAILS, DESCRIPTIONS, PACKAGINGS & LOT REFERENCES POPULATED SUCCESSFULLY!")

if __name__ == '__main__':
    run()
