#!/usr/bin/env python3
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'big_frozen_food'

def run():
    odoo.tools.config.parse_config(['-c', '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf', '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print("=== POPULATING RICH EXECUTIVE DASHBOARD DEMO DATA ===")

        vendors = env['res.partner'].search([('supplier_rank', '>', 0)])
        products = env['product.product'].search([('is_storable', '=', True)])
        resellers = env['res.partner'].search([('name', 'ilike', 'Reseller')])
        agens = env['res.partner'].search([('name', 'ilike', 'Agen')])
        customers_umum = env['res.partner'].search([('name', 'ilike', 'Umum')], limit=1) or env['res.partner'].search([], limit=1)
        pos_config = env['pos.config'].search([('name', '=', 'Big Frozen Food POS')], limit=1) or env['pos.config'].search([], limit=1)
        pm_cash = env['pos.payment.method'].search([('name', 'ilike', 'Cash')], limit=1) or env['pos.payment.method'].search([], limit=1)

        b2b_customers = list(resellers) + list(agens)
        if not b2b_customers:
            b2b_customers = [customers_umum]

        start_date = datetime(2026, 7, 1, 9, 0, 0)
        today = datetime.now()

        # 1. Generate Purchase Orders (July - Aug 2026)
        print("\n--- 1. Generating Purchase Orders ---")
        po_count = 0
        for i in range(15):
            vendor = vendors[i % len(vendors)]
            po_date = start_date + timedelta(days=i * 4 + random.randint(0, 2))
            if po_date > today:
                po_date = today - timedelta(days=random.randint(1, 5))
            
            selected_prods = random.sample(list(products), k=min(len(products), random.randint(4, 8)))
            lines = []
            for p in selected_prods:
                qty = random.choice([50, 100, 150, 200])
                cost = p.standard_price or (p.list_price * 0.7) or 25000.0
                lines.append((0, 0, {
                    'product_id': p.id,
                    'name': p.display_name,
                    'product_qty': qty,
                    'product_uom': p.uom_id.id,
                    'price_unit': cost,
                    'date_planned': po_date,
                }))

            po = env['purchase.order'].create({
                'partner_id': vendor.id,
                'date_order': po_date,
                'order_line': lines,
            })
            try:
                po.button_confirm()
                for picking in po.picking_ids:
                    for move in picking.move_ids:
                        move.quantity = move.product_uom_qty
                    picking.button_validate()
            except Exception as e:
                print(f" Warning on PO confirm: {e}")
            po_count += 1

        print(f" SUCCESS: {po_count} POs created & validated.")

        # 2. Generate B2B Sales Orders (Agen / Reseller)
        print("\n--- 2. Generating B2B Sales Orders ---")
        so_count = 0
        for i in range(30):
            cust = b2b_customers[i % len(b2b_customers)]
            so_date = start_date + timedelta(days=i * 2 + random.randint(0, 1))
            if so_date > today:
                so_date = today - timedelta(hours=random.randint(1, 48))
            
            selected_prods = random.sample(list(products), k=min(len(products), random.randint(3, 6)))
            lines = []
            for p in selected_prods:
                qty = random.randint(10, 40)
                price = p.list_price or 45000.0
                lines.append((0, 0, {
                    'product_id': p.id,
                    'product_uom_qty': qty,
                    'product_uom': p.uom_id.id,
                    'price_unit': price,
                }))

            so = env['sale.order'].create({
                'partner_id': cust.id,
                'date_order': so_date,
                'order_line': lines,
            })
            try:
                so.action_confirm()
                for picking in so.picking_ids:
                    for move in picking.move_ids:
                        move.quantity = move.product_uom_qty
                    picking.button_validate()
            except Exception as e:
                print(f" Warning on SO confirm: {e}")
            so_count += 1

        print(f" SUCCESS: {so_count} Sales Orders created & validated.")

        # 3. Generate Retail POS Orders
        print("\n--- 3. Generating Retail POS Orders ---")
        pos_count = 0
        
        # Get payment method from POS config (bukan search global)
        if pos_config and pos_config.payment_method_ids:
            pm_cash = pos_config.payment_method_ids[0]
        else:
            pm_cash = env['pos.payment.method'].search([('name', 'ilike', 'Cash')], limit=1)

        session = env['pos.session'].search([('config_id', '=', pos_config.id), ('state', '=', 'opened')], limit=1)
        if not session:
            try:
                session = env['pos.session'].create({
                    'config_id': pos_config.id,
                    'user_id': SUPERUSER_ID,
                })
                session.action_pos_session_open()
            except Exception as e:
                print(f" Warning: Could not open POS session: {e}")
                session = None

        if session and pm_cash:
            for i in range(40):
                p_date = start_date + timedelta(days=int(i * 1.2), hours=random.randint(9, 19))
                if p_date > today:
                    p_date = today - timedelta(hours=random.randint(1, 24))

                selected_prods = random.sample(list(products), k=min(len(products), random.randint(2, 5)))
                lines = []
                total_amt = 0.0
                for p in selected_prods:
                    qty = random.randint(1, 6)
                    price = p.list_price or 35000.0
                    subtotal = qty * price
                    total_amt += subtotal
                    lines.append((0, 0, {
                        'product_id': p.id,
                        'qty': qty,
                        'price_unit': price,
                        'price_subtotal': subtotal,
                        'price_subtotal_incl': subtotal,
                    }))

                try:
                    pos_order = env['pos.order'].create({
                        'session_id': session.id,
                        'partner_id': customers_umum.id,
                        'date_order': p_date,
                        'amount_total': total_amt,
                        'amount_tax': 0.0,
                        'amount_paid': total_amt,
                        'amount_return': 0.0,
                        'lines': lines,
                        'payment_ids': [(0, 0, {
                            'payment_method_id': pm_cash.id,
                            'amount': total_amt,
                            'payment_date': p_date,
                        })],
                        'state': 'paid',
                    })
                    pos_count += 1
                except Exception as e:
                    print(f" Warning on POS order: {e}")
        else:
            print(" Skipping POS orders - no session or payment method available.")

        print(f" SUCCESS: {pos_count} POS Orders generated.")

        # 4. Set Low Stock & Near Expiry Lots (FEFO)
        print("\n--- 4. Setting Low Stock & FEFO Expiry Data ---")
        for idx, prod in enumerate(products[:6]):
            try:
                prod.min_stock_alert_qty = 25.0
            except Exception as e:
                pass
            quants = env['stock.quant'].search([('product_id', '=', prod.id), ('location_id.usage', '=', 'internal')])
            if quants:
                quants[0].sudo().write({'quantity': random.randint(3, 12)})

        # Create/Update stock lots for FEFO Expiry
        fefo_count = 0
        for idx, prod in enumerate(products[:8]):
            lot_name = f"LOT-EXP2026-00{idx+1}"
            exp_date = today + timedelta(days=random.choice([-5, 8, 14, 22, 28]))
            lot = env['stock.lot'].search([('product_id', '=', prod.id), ('name', '=', lot_name)], limit=1)
            if not lot:
                lot_vals = {
                    'name': lot_name,
                    'product_id': prod.id,
                    'company_id': env.company.id,
                }
                if 'expiration_date' in env['stock.lot']._fields:
                    lot_vals['expiration_date'] = exp_date
                elif 'use_date' in env['stock.lot']._fields:
                    lot_vals['use_date'] = exp_date
                lot = env['stock.lot'].create(lot_vals)
            else:
                if 'expiration_date' in env['stock.lot']._fields:
                    lot.write({'expiration_date': exp_date})
                elif 'use_date' in env['stock.lot']._fields:
                    lot.write({'use_date': exp_date})
            fefo_count += 1

        print(f" SUCCESS: {fefo_count} FEFO Expiry lots configured.")

        cr.commit()
        print("\n=== POPULATION COMPLETED SUCCESSFULLY! ===")

if __name__ == '__main__':
    run()
