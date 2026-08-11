#!/usr/bin/env python3
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, '/home/setyo/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'big_frozen_food'

def run():
    odoo.tools.config.parse_config(['-c', '/home/setyo/developer/odoo/odoo-BigFrozenFood/big_frozen_food.conf', '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print("=== POPULATING BULK TRANSACTIONS (PURCHASES, SALES ORDERS, INVOICES, POS) ===")

        # 1. Fetch Master Data
        vendors = env['res.partner'].search([('supplier_rank', '>', 0)])
        products = env['product.product'].search([('is_storable', '=', True)])
        customers_umum = env['res.partner'].search([('name', 'ilike', 'Umum')])
        resellers = env['res.partner'].search([('name', 'ilike', 'Reseller Frozen')])
        agens = env['res.partner'].search([('name', 'ilike', 'Agen Frozen Food')])
        pos_config = env['pos.config'].search([('name', '=', 'Big Frozen Food POS')], limit=1)

        assert vendors and products and resellers and agens and pos_config, "Master data incomplete! Run populate_master_data.py first."

        pl_public = env['product.pricelist'].search([('name', 'ilike', 'Umum')], limit=1)
        pl_reseller = env['product.pricelist'].search([('name', '=', 'Reseller Pricelist')], limit=1)
        pl_agen = env['product.pricelist'].search([('name', '=', 'Agen Pricelist')], limit=1)

        pm_cash = env['pos.payment.method'].search([('name', '=', 'Cash (BFF)')], limit=1)
        pm_transfer = env['pos.payment.method'].search([('name', '=', 'Bank Transfer (BFF)')], limit=1)
        pm_qris = env['pos.payment.method'].search([('name', '=', 'QRIS (BFF)')], limit=1)

        # ---------------------------------------------------------
        # 2. BULK PURCHASES (Procurement for Stocking up thousands of items)
        # ---------------------------------------------------------
        print("\n--- Generating 10 Bulk Purchase Orders & Stock Inbounds ---")
        base_date = datetime(2026, 7, 1, 9, 0, 0)
        
        po_count = 0
        total_inbound_qty = 0
        
        for i in range(10):
            vendor = vendors[i % len(vendors)]
            po_date = base_date + timedelta(days=i * 3 + random.randint(0, 1))
            
            # Select 6-12 random products for each PO
            selected_products = random.sample(list(products), k=random.randint(6, 12))
            order_lines = []
            
            for prod in selected_products:
                qty = random.choice([100, 150, 200, 300, 500])
                total_inbound_qty += qty
                order_lines.append((0, 0, {
                    'product_id': prod.id,
                    'name': prod.display_name,
                    'product_qty': qty,
                    'product_uom': prod.uom_id.id,
                    'price_unit': prod.standard_price or (prod.list_price * 0.65),
                    'date_planned': po_date,
                }))

            po = env['purchase.order'].create({
                'partner_id': vendor.id,
                'date_order': po_date,
                'order_line': order_lines,
            })
            po.button_confirm()

            # Process Receipt (Validate Stock)
            for picking in po.picking_ids:
                for move in picking.move_ids:
                    move.quantity = move.product_uom_qty
                picking.button_validate()

            po_count += 1
            print(f" [PO #{po_count}] {po.name} - Vendor: {vendor.name} | Items: {len(selected_products)} | Date: {po_date.strftime('%Y-%m-%d')}")

        print(f" SUCCESS: {po_count} POs validated! Total Inbound Stock Added: {total_inbound_qty:,} units.")

        # ---------------------------------------------------------
        # 3. BULK B2B SALES ORDERS & INVOICES (Agen & Reseller Orders)
        # ---------------------------------------------------------
        print("\n--- Generating 15 Bulk B2B Sales Orders & Invoices ---")
        so_count = 0
        inv_count = 0

        all_b2b_customers = list(resellers) + list(agens)
        
        for i in range(15):
            cust = all_b2b_customers[i % len(all_b2b_customers)]
            so_date = base_date + timedelta(days=i * 2 + 1)
            
            # Pick 4-8 products
            selected_products = random.sample(list(products), k=random.randint(4, 8))
            so_lines = []
            
            for prod in selected_products:
                qty = random.randint(15, 60)
                # Apply pricelist price
                pricelist = cust.property_product_pricelist or pl_public
                price = pricelist._get_product_price(prod, qty)
                
                so_lines.append((0, 0, {
                    'product_id': prod.id,
                    'product_uom_qty': qty,
                    'price_unit': price,
                }))

            so = env['sale.order'].create({
                'partner_id': cust.id,
                'date_order': so_date,
                'order_line': so_lines,
            })
            so.action_confirm()

            # Deliver items (Stock Outbound)
            for picking in so.picking_ids:
                for move in picking.move_ids:
                    move.quantity = move.product_uom_qty
                picking.button_validate()

            # Generate Invoice
            inv = so._create_invoices()
            inv.action_post()

            so_count += 1
            inv_count += 1
            print(f" [SO #{so_count}] {so.name} -> Inv: {inv.name} | Customer: {cust.name} | Total: Rp {inv.amount_total:,.0f}")

        # ---------------------------------------------------------
        # 4. BULK POS SESSIONS & TRANSACTIONS (Retail & Wholesale POS)
        # ---------------------------------------------------------
        print("\n--- Generating Bulk POS Sessions & 35 Transactions ---")
        
        pos_order_count = 0
        pos_revenue = 0

        # Close any lingering active sessions first
        open_sessions = env['pos.session'].search([('config_id', '=', pos_config.id), ('state', '!=', 'closed')])
        for s in open_sessions:
            if s.state == 'opened':
                s.action_pos_session_closing_control()
            s.unlink()

        # Generate 4 distinct POS Sessions (Simulating multi-day / multi-shift cash registers)
        for s_idx in range(1, 5):
            session_date = base_date + timedelta(days=s_idx * 7)
            session = env['pos.session'].create({
                'config_id': pos_config.id,
                'user_id': SUPERUSER_ID,
                'start_at': session_date,
            })
            session.action_pos_session_open()
            print(f"\n POS Session #{s_idx} Active: {session.name}")

            # 8-10 transactions per session
            tx_per_session = random.randint(8, 10)
            for t_idx in range(tx_per_session):
                # Pick customer (30% Umum, 40% Reseller, 30% Agen)
                rnd_tier = random.random()
                if rnd_tier < 0.3:
                    cust = customers_umum[random.randint(0, len(customers_umum) - 1)]
                    pricelist = pl_public
                    pm = pm_cash
                    qty_mult = 1
                elif rnd_tier < 0.7:
                    cust = resellers[random.randint(0, len(resellers) - 1)]
                    pricelist = pl_reseller
                    pm = random.choice([pm_transfer, pm_qris])
                    qty_mult = 5
                else:
                    cust = agens[random.randint(0, len(agens) - 1)]
                    pricelist = pl_agen
                    pm = random.choice([pm_transfer, pm_qris, pm_cash])
                    qty_mult = 10

                selected_prods = random.sample(list(products), k=random.randint(2, 5))
                pos_lines = []
                order_total = 0.0

                for prod in selected_prods:
                    qty = random.randint(1, 5) * qty_mult
                    price_unit = pricelist._get_product_price(prod, qty)
                    subtotal = price_unit * qty
                    order_total += subtotal

                    pos_lines.append((0, 0, {
                        'product_id': prod.id,
                        'qty': qty,
                        'price_unit': price_unit,
                        'price_subtotal': subtotal,
                        'price_subtotal_incl': subtotal,
                    }))

                pos_order = env['pos.order'].create({
                    'session_id': session.id,
                    'partner_id': cust.id,
                    'pricelist_id': pricelist.id,
                    'lines': pos_lines,
                    'amount_total': order_total,
                    'amount_tax': 0,
                    'amount_paid': order_total,
                    'amount_return': 0,
                    'payment_ids': [(0, 0, {
                        'payment_method_id': pm.id,
                        'amount': order_total,
                    })],
                })
                pos_order.action_pos_order_paid()
                pos_order._create_order_picking()

                pos_order_count += 1
                pos_revenue += order_total

            # Close Session
            session.action_pos_session_closing_control()
            print(f" Session {session.name} Closed cleanly. Orders in session: {tx_per_session}")

        print(f"\n SUCCESS: {pos_order_count} POS Transactions created across 4 sessions! Total POS Revenue: Rp {pos_revenue:,.0f}")

        cr.commit()
        print("\n=======================================================")
        print("   BULK TRANSACTION GENERATION COMPLETED SUCCESSFULLY!  ")
        print("=======================================================")

if __name__ == '__main__':
    run()
