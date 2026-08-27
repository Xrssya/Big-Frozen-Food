# -*- coding: utf-8 -*-
import sys
import os
import random
from datetime import datetime, timedelta, date

# Odoo setup environment
import odoo
from odoo import api, SUPERUSER_ID

def run_for_db(db_name):
    print(f"\n=======================================================")
    print(f"   POPULATING BRANCHES & DEMO DATA FOR DB: {db_name}")
    print(f"=======================================================")
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'big_frozen_food.conf')
    odoo.tools.config.parse_config(['-c', config_file, '-d', db_name])
    registry = odoo.registry(db_name)

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        main_company = env['res.company'].search([('name', 'ilike', 'Big Frozen Food')], limit=1)
        if not main_company:
            main_company = env['res.company'].create({'name': 'Big Frozen Food'})

        branches_data = [
            {'name': 'Big Frozen Food - SBY', 'city': 'Surabaya', 'quiet_day': 1},   # Tuesday (0=Mon, 1=Tue)
            {'name': 'Big Frozen Food - MLG', 'city': 'Malang', 'quiet_day': 2},     # Wednesday
            {'name': 'Big Frozen Food - SDA', 'city': 'Sidoarjo', 'quiet_day': 0},   # Monday
            {'name': 'Big Frozen Food - GSK', 'city': 'Gresik', 'quiet_day': 3},     # Thursday
            {'name': 'Big Frozen Food - JKT', 'city': 'Jakarta', 'quiet_day': 1},    # Tuesday
            {'name': 'Big Frozen Food - SMG', 'city': 'Semarang', 'quiet_day': 2},   # Wednesday
        ]

        created_branches = {}
        for b_info in branches_data:
            comp = env['res.company'].search([('name', '=', b_info['name'])], limit=1)
            if not comp:
                comp = env['res.company'].create({
                    'name': b_info['name'],
                    'parent_id': main_company.id,
                    'city': b_info['city'],
                    'currency_id': env.ref('base.IDR').id if env.ref('base.IDR', raise_if_not_found=False) else main_company.currency_id.id
                })
                print(f"Created branch company: {comp.name}")
            else:
                print(f"Existing branch company: {comp.name}")

            created_branches[b_info['name']] = {
                'company': comp,
                'quiet_day': b_info['quiet_day']
            }

            # Ensure warehouse
            wh = env['stock.warehouse'].search([('company_id', '=', comp.id)], limit=1)
            if not wh:
                code_prefix = b_info['city'][:3].upper()
                env['stock.warehouse'].create({
                    'name': f"Gudang {b_info['name']}",
                    'code': code_prefix,
                    'company_id': comp.id
                })
                print(f"Created Warehouse for {comp.name}")

            # Ensure Cash Journal for Company
            cash_journal = env['account.journal'].search([
                ('company_id', '=', comp.id),
                ('type', '=', 'cash')
            ], limit=1)
            if not cash_journal:
                cash_journal = env['account.journal'].create({
                    'name': f"Kas {b_info['city']}",
                    'code': f"CSH{b_info['city'][:2].upper()}",
                    'type': 'cash',
                    'company_id': comp.id
                })

            # Ensure POS Payment Method for Company
            pay_method = env['pos.payment.method'].search([
                ('company_id', '=', comp.id)
            ], limit=1)
            if not pay_method:
                pay_method = env['pos.payment.method'].create({
                    'name': f"Tunai / Cash {b_info['city']}",
                    'journal_id': cash_journal.id,
                    'company_id': comp.id
                })

            # Ensure Sale Journal for Company
            sale_journal = env['account.journal'].search([
                ('company_id', '=', comp.id),
                ('type', '=', 'sale')
            ], limit=1)
            if not sale_journal:
                sale_journal = env['account.journal'].create({
                    'name': f"Penjualan POS {b_info['city']}",
                    'code': f"POS{b_info['city'][:2].upper()}",
                    'type': 'sale',
                    'company_id': comp.id
                })

            # Ensure POS config
            pos_cfg = env['pos.config'].search([('company_id', '=', comp.id)], limit=1)
            if not pos_cfg:
                env['pos.config'].create({
                    'name': f"POS Kasir {b_info['name']}",
                    'company_id': comp.id,
                    'journal_id': sale_journal.id,
                    'invoice_journal_id': sale_journal.id,
                    'payment_method_ids': [(4, pay_method.id)]
                })
                print(f"Created POS Config for {comp.name}")

        cr.commit()

        # Create realistic demo transactions for the last 60 days
        products = env['product.product'].search([('type', '=', 'consu')], limit=10)
        if not products:
            products = env['product.product'].search([], limit=10)

        partners = env['res.partner'].search([('customer_rank', '>', 0)], limit=5)
        if not partners:
            partners = env['res.partner'].search([], limit=5)

        today = date.today()
        start_date = today - timedelta(days=60)

        print("\nPopulating realistic daily & hourly transaction patterns for popular times analytics...")
        pos_orders_created = 0

        # Hourly distribution weight profile (06:00 to 21:00)
        # Peak around 11-13 and 17-19
        hourly_weights = {
            6: 2, 7: 5, 8: 10, 9: 15, 10: 25, 11: 45, 12: 50, 13: 40,
            14: 30, 15: 35, 16: 45, 17: 65, 18: 80, 19: 75, 20: 40, 21: 15
        }

        for b_name, b_data in created_branches.items():
            comp = b_data['company']
            quiet_day = b_data['quiet_day'] # 0=Mon, 1=Tue, 2=Wed, etc.
            pos_cfg = env['pos.config'].search([('company_id', '=', comp.id)], limit=1)
            if not pos_cfg:
                continue

            session = env['pos.session'].search([('config_id', '=', pos_cfg.id)], limit=1)
            if not session:
                session = env['pos.session'].create({
                    'config_id': pos_cfg.id,
                    'user_id': SUPERUSER_ID,
                })
                session.action_pos_session_open()

            current_dt = start_date
            while current_dt <= today:
                day_of_week = current_dt.weekday() # 0=Mon, 1=Tue... 5=Sat, 6=Sun
                
                # Base volume factor by day of week
                if day_of_week == quiet_day:
                    # Very Quiet Day! Only ~15% volume
                    daily_target = random.randint(1, 4)
                elif day_of_week in [5, 6]:
                    # Weekend! Busiest day (150% volume)
                    daily_target = random.randint(25, 40)
                else:
                    # Regular weekday
                    daily_target = random.randint(12, 22)

                for _ in range(daily_target):
                    # Pick hour based on weights
                    hours = list(hourly_weights.keys())
                    weights = list(hourly_weights.values())
                    chosen_hour = random.choices(hours, weights=weights, k=1)[0]
                    chosen_min = random.randint(0, 59)
                    chosen_sec = random.randint(0, 59)

                    order_time = datetime.combine(current_dt, datetime.min.time()).replace(
                        hour=chosen_hour, minute=chosen_min, second=chosen_sec
                    )

                    # Create POS Order
                    prod = random.choice(products) if products else None
                    qty = random.randint(1, 4)
                    price_unit = prod.lst_price if prod and hasattr(prod, 'lst_price') and prod.lst_price > 0 else 25000.0
                    subtotal = qty * price_unit

                    partner = random.choice(partners) if partners else None

                    order_vals = {
                        'name': f"POS/{comp.name[:3]}/{order_time.strftime('%Y%m%d%H%M%S')}-{random.randint(100,999)}",
                        'company_id': comp.id,
                        'session_id': session.id,
                        'date_order': order_time,
                        'user_id': SUPERUSER_ID,
                        'amount_tax': 0.0,
                        'amount_total': subtotal,
                        'amount_paid': subtotal,
                        'amount_return': 0.0,
                        'state': 'done',
                        'partner_id': partner.id if partner else False,
                    }
                    
                    # Create pos order line
                    if prod:
                        order_vals['lines'] = [(0, 0, {
                            'product_id': prod.id,
                            'qty': qty,
                            'price_unit': price_unit,
                            'price_subtotal': subtotal,
                            'price_subtotal_incl': subtotal,
                        })]

                    try:
                        env['pos.order'].create(order_vals)
                        pos_orders_created += 1
                    except Exception as e:
                        pass

                current_dt += timedelta(days=1)
        
        cr.commit()
        print(f"Successfully populated {pos_orders_created} historical branch transactions across days of the week!")

def main():
    target_dbs = ['odoo-big-frozen', 'big_frozen_food']
    if len(sys.argv) > 1:
        target_dbs = [sys.argv[1]]
    for db in target_dbs:
        try:
            run_for_db(db)
        except Exception as e:
            print(f"Error for DB {db}: {e}")

if __name__ == '__main__':
    main()
