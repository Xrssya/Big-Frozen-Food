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
        print("=== VERIFYING BIG FROZEN FOOD ODOO 18 DATABASE ===")

        # 1. Company
        company = env['res.company'].search([('name', '=', 'Big Frozen Food')], limit=1)
        assert company, "Company Big Frozen Food not found!"
        assert company.logo, "Company logo is not set!"
        print(f" [PASS] Company: {company.name} | Logo Present: True | Phone: {company.phone}")

        # 2. Product Categories
        categories = env['product.category'].search([])
        cat_names = [c.name for c in categories]
        req_cats = ["Nugget", "Sosis", "Bakso & Olahan Daging", "Seafood", "Dimsum", "Kentang & Snack", "Ayam & Unggas", "Tempura & Olahan Seafood", "Produk Pelengkap"]
        for rc in req_cats:
            assert rc in cat_names, f"Category missing: {rc}"
        print(f" [PASS] Categories Count: {len(categories)} (All 9 required categories confirmed)")

        # 3. Products Master Data
        products = env['product.product'].search([('is_storable', '=', True)])
        assert len(products) >= 45, f"Expected at least 45 products, found {len(products)}"
        print(f" [PASS] Storable Products Count: {len(products)}")

        # 4. Customers & Vendors
        vendors = env['res.partner'].search([('supplier_rank', '>', 0)])
        assert len(vendors) >= 5, f"Expected at least 5 vendors, found {len(vendors)}"
        print(f" [PASS] Vendors Count: {len(vendors)}")

        customers_umum = env['res.partner'].search([('name', 'ilike', 'Umum')])
        resellers = env['res.partner'].search([('name', 'ilike', 'Reseller Frozen')])
        agens = env['res.partner'].search([('name', 'ilike', 'Agen Frozen Food')])
        print(f" [PASS] Customer Tiers - Umum: {len(customers_umum)}, Resellers: {len(resellers)}, Agens: {len(agens)}")
        assert len(resellers) >= 10, "Reseller count < 10!"
        assert len(agens) >= 10, "Agen count < 10!"

        # 5. Pricelists Verification
        pl_public = env['product.pricelist'].search([('name', 'ilike', 'Umum')], limit=1)
        pl_reseller = env['product.pricelist'].search([('name', '=', 'Reseller Pricelist')], limit=1)
        pl_agen = env['product.pricelist'].search([('name', '=', 'Agen Pricelist')], limit=1)

        assert pl_public and pl_reseller and pl_agen, "One of 3 pricelists is missing!"

        # Test specific price matrix for Nugget Ayam Original 500g
        nugget = env['product.product'].search([('name', '=', 'Nugget Ayam Original 500g')], limit=1)
        p_pub = pl_public._get_product_price(nugget, 1.0)
        p_res = pl_reseller._get_product_price(nugget, 1.0)
        p_age = pl_agen._get_product_price(nugget, 1.0)

        print(f" [PASS] Pricelist Matrix for Nugget Ayam Original 500g:")
        print(f"        Public: Rp {p_pub:,.0f} | Reseller: Rp {p_res:,.0f} | Agen: Rp {p_age:,.0f}")
        assert p_pub == 35000, f"Expected 35000, got {p_pub}"
        assert p_res == 32000, f"Expected 32000, got {p_res}"
        assert p_age == 29000, f"Expected 29000, got {p_age}"

        # 6. Inventory Stock On Hand Verification
        stock_quants = env['stock.quant'].search([('product_id', '=', nugget.id), ('location_id.usage', '=', 'internal')])
        total_qty = sum(stock_quants.mapped('quantity'))
        print(f" [PASS] Stock On Hand for Nugget Ayam Original 500g: {total_qty} units (Post 72 pcs POS Sales)")
        assert total_qty == 28.0, f"Expected 28.0 units remaining stock after POS sales, got {total_qty}"

        # 7. POS Config
        pos_config = env['pos.config'].search([('name', '=', 'Big Frozen Food POS')], limit=1)
        assert pos_config, "POS Config Big Frozen Food POS not found!"
        print(f" [PASS] POS Configuration: {pos_config.name}")

        # 8. Promotion Verification
        promo_pl = env['product.pricelist'].search([('name', 'ilike', 'Promo Kemerdekaan')], limit=1)
        assert promo_pl, "Promo Kemerdekaan not found!"
        print(f" [PASS] Promotion: {promo_pl.name} configured.")

        print("=== ALL VERIFICATION CHECKS PASSED SUCCESSFULLY ===")

if __name__ == '__main__':
    run()
