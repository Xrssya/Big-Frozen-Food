#!/usr/bin/env python3
import sys

sys.path.insert(0, '/home/rsya/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'big_frozen_food'

def run():
    odoo.tools.config.parse_config(['-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print("=== GENERATING DEMO SALES ORDERS & INVOICES FOR CONTINUOUS FORM PREVIEW ===")

        partner_agen = env['res.partner'].search([('name', '=', 'Agen Frozen Food Pasuruan')], limit=1)
        partner_reseller = env['res.partner'].search([('name', '=', 'Reseller Frozen Pasuruan')], limit=1)

        p_nugget = env['product.product'].search([('name', '=', 'Nugget Ayam Original 500g')], limit=1)
        p_sosis = env['product.product'].search([('name', '=', 'Sosis Ayam 500g')], limit=1)
        p_fries = env['product.product'].search([('name', '=', 'French Fries Shoestring 1kg')], limit=1)

        # Sales Order 1 (Agen Pasuruan)
        so1 = env['sale.order'].create({
            'partner_id': partner_agen.id,
            'order_line': [
                (0, 0, {'product_id': p_nugget.id, 'product_uom_qty': 50, 'price_unit': 29000}),
                (0, 0, {'product_id': p_sosis.id, 'product_uom_qty': 50, 'price_unit': 25000}),
                (0, 0, {'product_id': p_fries.id, 'product_uom_qty': 30, 'price_unit': 26000}),
            ]
        })
        so1.action_confirm()

        # Create Invoice for SO1
        invoice1 = so1._create_invoices()
        invoice1.action_post()
        print(f" Demo Invoice {invoice1.name} created for {partner_agen.name} (Total: Rp {invoice1.amount_total:,.0f})")

        # Sales Order 2 (Reseller Pasuruan)
        so2 = env['sale.order'].create({
            'partner_id': partner_reseller.id,
            'order_line': [
                (0, 0, {'product_id': p_nugget.id, 'product_uom_qty': 20, 'price_unit': 32000}),
                (0, 0, {'product_id': p_sosis.id, 'product_uom_qty': 20, 'price_unit': 27500}),
            ]
        })
        so2.action_confirm()

        invoice2 = so2._create_invoices()
        invoice2.action_post()
        print(f" Demo Invoice {invoice2.name} created for {partner_reseller.name} (Total: Rp {invoice2.amount_total:,.0f})")

        cr.commit()
        print("=== DEMO SALES ORDERS & INVOICES CREATED SUCCESSFULLY ===")

if __name__ == '__main__':
    run()
