#!/usr/bin/env python3
import sys
import base64
import os
import logging
path
sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'big_frozen_food'

def run():
    odoo.tools.config.parse_config(['-c', '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf', '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print(" Connected to Odoo 18 environment for database:", DB_NAME)

        # 1. Company Setup
        company = env['res.company'].search([], limit=1)
        idr = env['res.currency'].with_context(active_test=False).search([('name', '=', 'IDR')], limit=1)
        if idr:
            idr.write({'active': True, 'symbol': 'Rp', 'position': 'before'})
            currency_id = idr.id
        else:
            currency_id = company.currency_id.id

        company.write({
            'name': 'Big Frozen Food',
            'street': 'Jl. Contoh No. 123',
            'city': 'Pasuruan',
            'state_id': env['res.country.state'].search([('name', '=', 'Jawa Timur')], limit=1).id or False,
            'zip': '67111',
            'phone': '08xx-xxxx-xxxx',
            'email': 'info@bigfrozenfood.example',
            'website': 'www.bigfrozenfood.example',
            'currency_id': currency_id,
        })
        print(f" Company updated: Big Frozen Food (Main Currency: {company.currency_id.name})")

        # 1b. Logo
        logo_path = '/home/adi-purwanto/.gemini/antigravity-ide/brain/e1380b57-9c9f-4a04-a671-291c8c166c51/big_frozen_food_logo_1786343821764.png'
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_b64 = base64.b64encode(f.read())
                company.write({'logo': logo_b64})
                print(" Logo set on company record.")

        # 2. Product Categories (9 required)
        category_names = [
            "Nugget",
            "Sosis",
            "Bakso & Olahan Daging",
            "Seafood",
            "Dimsum",
            "Kentang & Snack",
            "Ayam & Unggas",
            "Tempura & Olahan Seafood",
            "Produk Pelengkap"
        ]
        cat_map = {}
        for cat_name in category_names:
            cat = env['product.category'].search([('name', '=', cat_name)], limit=1)
            if not cat:
                cat = env['product.category'].create({'name': cat_name})
            cat_map[cat_name] = cat.id
        print(f" {len(cat_map)} Product Categories ready.")

        # 3. Vendors (5 required)
        vendors_data = [
            "PT Frozen Makmur",
            "CV Sumber Pangan",
            "PT Indo Frozen",
            "CV Berkah Food",
            "PT Mitra Frozen"
        ]
        vendor_map = {}
        for v_name in vendors_data:
            v = env['res.partner'].search([('name', '=', v_name), ('supplier_rank', '>', 0)], limit=1)
            if not v:
                v = env['res.partner'].create({
                    'name': v_name,
                    'is_company': True,
                    'supplier_rank': 1,
                    'street': 'Jl. Industri Food No. ' + str(len(vendor_map) + 1),
                    'city': 'Surabaya',
                    'phone': f'031-778800{len(vendor_map)+1}',
                    'email': f'sales@{v_name.lower().replace(" ", "")}.example'
                })
            vendor_map[v_name] = v.id
        print(f" {len(vendor_map)} Vendors ready.")

        # 4. Products Master Data (45-50 products)
        products_def = [
            # Nugget
            ("Nugget Ayam Original 500g", "Nugget", 35000, 24000, "8991001000010"),
            ("Nugget Ayam Crispy 500g", "Nugget", 38000, 26000, "8991001000027"),
            ("Nugget Coin 500g", "Nugget", 33000, 22000, "8991001000034"),
            ("Nugget Stick 500g", "Nugget", 34000, 23000, "8991001000041"),
            ("Nugget Premium 500g", "Nugget", 42000, 29000, "8991001000058"),
            ("Nugget Cheese 500g", "Nugget", 40000, 28000, "8991001000065"),
            
            # Sosis
            ("Sosis Ayam 500g", "Sosis", 30000, 20000, "8991002000019"),
            ("Sosis Sapi 500g", "Sosis", 36000, 24000, "8991002000026"),
            ("Sosis Jumbo 500g", "Sosis", 45000, 31000, "8991002000033"),
            ("Sosis Cocktail 500g", "Sosis", 32000, 21000, "8991002000040"),
            ("Sosis Bratwurst 500g", "Sosis", 48000, 33000, "8991002000057"),
            ("Sosis Cheesy 500g", "Sosis", 38000, 26000, "8991002000064"),
            
            # Bakso & Olahan Daging
            ("Bakso Sapi Super 500g", "Bakso & Olahan Daging", 40000, 27000, "8991003000018"),
            ("Bakso Sapi Halus 500g", "Bakso & Olahan Daging", 35000, 23000, "8991003000025"),
            ("Bakso Urat 500g", "Bakso & Olahan Daging", 38000, 25000, "8991003000032"),
            ("Bakso Ayam 500g", "Bakso & Olahan Daging", 28000, 18000, "8991003000049"),
            ("Daging Slice Shortplate 500g", "Bakso & Olahan Daging", 65000, 47000, "8991003000056"),

            # Seafood
            ("Fish Roll 500g", "Seafood", 28000, 18000, "8991004000017"),
            ("Crab Stick 500g", "Seafood", 26000, 17000, "8991004000024"),
            ("Fish Dumpling Cheese 500g", "Seafood", 32000, 21000, "8991004000031"),
            ("Seafood Ball 500g", "Seafood", 30000, 20000, "8991004000048"),
            ("Ebi Furai 500g", "Seafood", 45000, 31000, "8991004000055"),
            ("Fish Cake 500g", "Seafood", 29000, 19000, "8991004000062"),

            # Dimsum
            ("Siomay Ayam 500g", "Dimsum", 35000, 23000, "8991005000016"),
            ("Siomay Udang 500g", "Dimsum", 40000, 27000, "8991005000023"),
            ("Hakau Udang 500g", "Dimsum", 42000, 28000, "8991005000030"),
            ("Gyoza Ayam 500g", "Dimsum", 36000, 24000, "8991005000047"),
            ("Dimsum Mix 500g", "Dimsum", 38000, 25000, "8991005000054"),

            # Kentang & Snack
            ("French Fries Shoestring 1kg", "Kentang & Snack", 32000, 21000, "8991006000015"),
            ("French Fries Crinkle 1kg", "Kentang & Snack", 33000, 22000, "8991006000022"),
            ("French Fries Shoestring 2kg", "Kentang & Snack", 60000, 40000, "8991006000039"),
            ("Potato Wedges 1kg", "Kentang & Snack", 36000, 24000, "8991006000046"),
            ("Hashbrown 1kg", "Kentang & Snack", 38000, 25000, "8991006000053"),

            # Ayam & Unggas
            ("Chicken Wings Original 500g", "Ayam & Unggas", 42000, 28000, "8991007000014"),
            ("Chicken Karaage 500g", "Ayam & Unggas", 45000, 30000, "8991007000021"),
            ("Chicken Popcorn 500g", "Ayam & Unggas", 38000, 25000, "8991007000038"),
            ("Chicken Strip 500g", "Ayam & Unggas", 40000, 27000, "8991007000045"),
            ("Chicken Katsu 500g", "Ayam & Unggas", 44000, 29000, "8991007000052"),

            # Tempura & Olahan Seafood
            ("Tempura Udang 500g", "Tempura & Olahan Seafood", 35000, 23000, "8991008000013"),
            ("Shrimp Roll 500g", "Tempura & Olahan Seafood", 38000, 25000, "8991008000020"),
            ("Otak-Otak Ikan 500g", "Tempura & Olahan Seafood", 25000, 16000, "8991008000037"),
            ("Scallop Singapore 500g", "Tempura & Olahan Seafood", 32000, 21000, "8991008000044"),

            # Produk Pelengkap
            ("Mayonaise Original 1kg", "Produk Pelengkap", 28000, 18000, "8991009000012"),
            ("Saus Sambal Extra Pedas 1kg", "Produk Pelengkap", 24000, 15000, "8991009000029"),
            ("Saus Tomat 1kg", "Produk Pelengkap", 22000, 14000, "8991009000036"),
            ("Saus Keju 500g", "Produk Pelengkap", 26000, 17000, "8991009000043"),
            ("Bumbu Tabur Balado 250g", "Produk Pelengkap", 15000, 9000, "8991009000050"),
        ]

        prod_map = {}
        for p_name, p_cat, p_price, p_cost, p_barcode in products_def:
            p = env['product.product'].search([('name', '=', p_name)], limit=1)
            if not p:
                p = env['product.product'].create({
                    'name': p_name,
                    'categ_id': cat_map[p_cat],
                    'is_storable': True,
                    'list_price': p_price,
                    'standard_price': p_cost,
                    'barcode': p_barcode,
                    'available_in_pos': True,
                })
            prod_map[p_name] = p
        print(f" {len(prod_map)} Products populated.")

        # Enable multi-pricelist setting via group assignment
        try:
            pricelist_group = env.ref('product.group_product_pricelist')
            user_group = env.ref('base.group_user')
            system_group = env.ref('base.group_system')
            if pricelist_group:
                user_group.write({'implied_ids': [(4, pricelist_group.id)]})
                system_group.write({'implied_ids': [(4, pricelist_group.id)]})
                # Add all active users to pricelist group
                for u in env['res.users'].search([]):
                    u.write({'groups_id': [(4, pricelist_group.id)]})
        except Exception as e:
            print(" Note on setting multi-pricelist group:", e)

        # 5. Native Pricelists Setup
        pl_public = env['product.pricelist'].search([('name', 'ilike', 'Umum')], limit=1) or \
                    env['product.pricelist'].search([('name', 'ilike', 'Public')], limit=1)
        if not pl_public:
            pl_public = env['product.pricelist'].create({'name': 'Umum / Public Pricelist'})
        else:
            pl_public.write({'name': 'Umum / Public Pricelist'})

        pl_reseller = env['product.pricelist'].search([('name', '=', 'Reseller Pricelist')], limit=1)
        if not pl_reseller:
            pl_reseller = env['product.pricelist'].create({'name': 'Reseller Pricelist'})

        pl_agen = env['product.pricelist'].search([('name', '=', 'Agen Pricelist')], limit=1)
        if not pl_agen:
            pl_agen = env['product.pricelist'].create({'name': 'Agen Pricelist'})

        # Define explicit product price overrides for key demo products
        explicit_pricing = {
            "Nugget Ayam Original 500g": {"Umum": 35000, "Reseller": 32000, "Agen": 29000},
            "Sosis Ayam 500g": {"Umum": 30000, "Reseller": 27500, "Agen": 25000},
            "French Fries Shoestring 1kg": {"Umum": 32000, "Reseller": 29000, "Agen": 26000},
            "Fish Roll 500g": {"Umum": 28000, "Reseller": 25000, "Agen": 23000},
        }

        for p_name, prices in explicit_pricing.items():
            prod = prod_map[p_name]
            # Reseller item rule
            item_r = env['product.pricelist.item'].search([('pricelist_id', '=', pl_reseller.id), ('product_id', '=', prod.id)], limit=1)
            if not item_r:
                env['product.pricelist.item'].create({
                    'pricelist_id': pl_reseller.id,
                    'applied_on': '0_product_variant',
                    'product_id': prod.id,
                    'compute_price': 'fixed',
                    'fixed_price': prices["Reseller"],
                })
            else:
                item_r.write({'compute_price': 'fixed', 'fixed_price': prices["Reseller"]})

            # Agen item rule
            item_a = env['product.pricelist.item'].search([('pricelist_id', '=', pl_agen.id), ('product_id', '=', prod.id)], limit=1)
            if not item_a:
                env['product.pricelist.item'].create({
                    'pricelist_id': pl_agen.id,
                    'applied_on': '0_product_variant',
                    'product_id': prod.id,
                    'compute_price': 'fixed',
                    'fixed_price': prices["Agen"],
                })
            else:
                item_a.write({'compute_price': 'fixed', 'fixed_price': prices["Agen"]})

        # Add generic fallback item for other products in Reseller (~10% off) and Agen (~18% off)
        if not env['product.pricelist.item'].search([('pricelist_id', '=', pl_reseller.id), ('applied_on', '=', '3_global')], limit=1):
            env['product.pricelist.item'].create({
                'pricelist_id': pl_reseller.id,
                'applied_on': '3_global',
                'compute_price': 'formula',
                'price_discount': 10.0,
            })
        if not env['product.pricelist.item'].search([('pricelist_id', '=', pl_agen.id), ('applied_on', '=', '3_global')], limit=1):
            env['product.pricelist.item'].create({
                'pricelist_id': pl_agen.id,
                'applied_on': '3_global',
                'compute_price': 'formula',
                'price_discount': 18.0,
            })

        print(" 3-Level Pricelists configured with explicit demo pricing matrix.")

        # 6. Customer Master Data (25 Partners across 3 tiers)
        partner_umum_default = env['res.partner'].search([('name', '=', 'Pembeli Umum')], limit=1)
        if not partner_umum_default:
            partner_umum_default = env['res.partner'].create({
                'name': 'Pembeli Umum',
                'property_product_pricelist': pl_public.id,
            })

        for i in range(1, 5):
            name = f"Customer Umum 0{i}"
            if not env['res.partner'].search([('name', '=', name)], limit=1):
                env['res.partner'].create({
                    'name': name,
                    'property_product_pricelist': pl_public.id,
                })

        reseller_cities = ["Pasuruan", "Bangil", "Pandaan", "Malang", "Sidoarjo", "Surabaya", "Gresik", "Mojokerto", "Jombang", "Probolinggo"]
        for city in reseller_cities:
            name = f"Reseller Frozen {city}"
            p = env['res.partner'].search([('name', '=', name)], limit=1)
            if not p:
                p = env['res.partner'].create({
                    'name': name,
                    'is_company': True,
                    'city': city,
                    'property_product_pricelist': pl_reseller.id,
                })
            else:
                p.write({'property_product_pricelist': pl_reseller.id})

        agen_cities = ["Pasuruan", "Malang", "Bangil", "Pandaan", "Sidoarjo", "Surabaya", "Gresik", "Mojokerto", "Jombang", "Probolinggo"]
        for city in agen_cities:
            name = f"Agen Frozen Food {city}"
            p = env['res.partner'].search([('name', '=', name)], limit=1)
            if not p:
                p = env['res.partner'].create({
                    'name': name,
                    'is_company': True,
                    'city': city,
                    'property_product_pricelist': pl_agen.id,
                })
            else:
                p.write({'property_product_pricelist': pl_agen.id})

        print(" 25 Customers across 3 tiers created and mapped to pricelists.")

        # 7. Purchase Workflow & Initial Inventory Stock
        po_plans = [
            ("PT Frozen Makmur", [
                ("Nugget Ayam Original 500g", 100),
                ("Nugget Ayam Crispy 500g", 80),
                ("Sosis Ayam 500g", 100),
                ("Sosis Sapi 500g", 80),
            ]),
            ("CV Sumber Pangan", [
                ("French Fries Shoestring 1kg", 100),
                ("Chicken Wings Original 500g", 60),
                ("Chicken Karaage 500g", 60),
            ]),
            ("PT Indo Frozen", [
                ("Fish Roll 500g", 80),
                ("Dimsum Mix 500g", 50),
                ("Ebi Furai 500g", 60),
            ]),
        ]

        for vendor_name, line_items in po_plans:
            vendor_id = vendor_map[vendor_name]
            po = env['purchase.order'].create({
                'partner_id': vendor_id,
                'order_line': [(0, 0, {
                    'product_id': prod_map[p_name].id,
                    'name': p_name,
                    'product_qty': qty,
                    'product_uom': prod_map[p_name].uom_id.id,
                    'price_unit': prod_map[p_name].standard_price,
                    'date_planned': odoo.fields.Datetime.now(),
                }) for p_name, qty in line_items]
            })
            po.button_confirm()
            for picking in po.picking_ids:
                for move in picking.move_ids:
                    move.quantity = move.product_uom_qty
                picking.button_validate()
        print(" Purchase Orders created and receipts validated. Initial stock added.")

        # 8. POS Session Setup
        pos_config = env['pos.config'].search([('name', '=', 'Big Frozen Food POS')], limit=1)
        if not pos_config:
            pos_config = env['pos.config'].create({
                'name': 'Big Frozen Food POS',
                'use_pricelist': True,
                'available_pricelist_ids': [(6, 0, [pl_public.id, pl_reseller.id, pl_agen.id])],
                'pricelist_id': pl_public.id,
                'receipt_header': '<center><h3>BIG FROZEN FOOD</h3><p>Jl. Contoh No. 123, Pasuruan</p></center>',
                'receipt_footer': '<center><p>Terima Kasih Atas Kunjungan Anda!</p></center>',
            })
        print(" POS Config 'Big Frozen Food POS' configured.")

        # 9. Promotion (Promo Kemerdekaan)
        promo_name = "Promo Kemerdekaan (10% Nugget)"
        promo_pr = env['product.pricelist'].search([('name', '=', promo_name)], limit=1)
        if not promo_pr:
            promo_pr = env['product.pricelist'].create({
                'name': promo_name,
                'item_ids': [(0, 0, {
                    'applied_on': '2_product_category',
                    'categ_id': cat_map["Nugget"],
                    'compute_price': 'formula',
                    'price_discount': 10.0,
                    'date_start': '2026-08-10',
                    'date_end': '2026-08-17',
                })]
            })
        print(" Promo Kemerdekaan (10% discount 10-17 Aug) created.")

        cr.commit()
        print(" SUCCESS: Big Frozen Food database population script completed cleanly!")

if __name__ == '__main__':
    run()
