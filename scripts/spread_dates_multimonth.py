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
        print("=== DISTRIBUTING DATES ACROSS MAY, JUNE, JULY, AUGUST 2026 ===")

        # 1. Update Sales Orders (date_order & create_date)
        sales_orders = env['sale.order'].search([])
        print(f" Found {len(sales_orders)} Sales Orders to distribute.")
        
        # Spread dates across May (5), June (6), July (7), August (8)
        months_dates = [
            (datetime(2026, 5, 5), datetime(2026, 5, 28)),
            (datetime(2026, 6, 2), datetime(2026, 6, 27)),
            (datetime(2026, 7, 2), datetime(2026, 7, 29)),
            (datetime(2026, 8, 1), datetime(2026, 8, 10)),
        ]

        for idx, so in enumerate(sales_orders):
            m_start, m_end = months_dates[idx % len(months_dates)]
            delta_days = (m_end - m_start).days
            rnd_days = random.randint(0, max(0, delta_days))
            target_date = m_start + timedelta(days=rnd_days, hours=random.randint(8, 16))

            # Direct SQL update for date_order, create_date to bypass action_confirm overrides
            cr.execute("""
                UPDATE sale_order 
                SET date_order = %s, create_date = %s
                WHERE id = %s
            """, (target_date, target_date, so.id))

            # Also update lines
            cr.execute("""
                UPDATE sale_order_line
                SET create_date = %s
                WHERE order_id = %s
            """, (target_date, so.id))

        # 2. Update Invoices (invoice_date, date, create_date)
        invoices = env['account.move'].search([('move_type', 'in', ['out_invoice', 'in_invoice'])])
        print(f" Found {len(invoices)} Invoices/Bills to distribute.")

        for idx, inv in enumerate(invoices):
            if inv.line_ids:
                so = env['sale.order'].search([('name', '=', inv.invoice_origin)], limit=1)
                if so:
                    target_date = so.date_order
                else:
                    m_start, m_end = months_dates[idx % len(months_dates)]
                    target_date = m_start + timedelta(days=random.randint(0, 15))

                target_str = target_date.strftime('%Y-%m-%d')
                cr.execute("""
                    UPDATE account_move
                    SET invoice_date = %s, date = %s, create_date = %s
                    WHERE id = %s
                """, (target_str, target_str, target_date, inv.id))

        # 3. Update POS Orders (date_order & create_date)
        pos_orders = env['pos.order'].search([])
        print(f" Found {len(pos_orders)} POS Orders to distribute.")

        for idx, po in enumerate(pos_orders):
            m_start, m_end = months_dates[idx % len(months_dates)]
            delta_days = (m_end - m_start).days
            target_date = m_start + timedelta(days=random.randint(0, max(0, delta_days)), hours=random.randint(8, 20))

            cr.execute("""
                UPDATE pos_order
                SET date_order = %s, create_date = %s
                WHERE id = %s
            """, (target_date, target_date, po.id))

            cr.execute("""
                UPDATE pos_order_line
                SET create_date = %s
                WHERE order_id = %s
            """, (target_date, po.id))

        # 4. Update Purchase Orders (date_order, date_approve, create_date)
        purchase_orders = env['purchase.order'].search([])
        print(f" Found {len(purchase_orders)} Purchase Orders to distribute.")

        for idx, po in enumerate(purchase_orders):
            m_start, m_end = months_dates[idx % len(months_dates)]
            target_date = m_start + timedelta(days=random.randint(0, 20), hours=random.randint(8, 16))

            cr.execute("""
                UPDATE purchase_order
                SET date_order = %s, date_approve = %s, create_date = %s
                WHERE id = %s
            """, (target_date, target_date, target_date, po.id))

        # 5. Flush reporting views in Odoo if any
        cr.commit()
        print("=== SUCCESS: DATES DISTRIBUTED ACROSS MEI, JUNI, JULI, AGUSTUS 2026 ===")

if __name__ == '__main__':
    run()
