#!/usr/bin/env python3
import sys

sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'big_frozen_food'

def run():
    odoo.tools.config.parse_config(['-c', '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf', '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        company = env['res.company'].search([('name', '=', 'Big Frozen Food')], limit=1)
        assert company, "Company Big Frozen Food not found!"
        env = api.Environment(cr, SUPERUSER_ID, {'allowed_company_ids': [company.id]})
        print("=== EXECUTING POS DEMO TRANSACTIONS ===")

        pos_config = env['pos.config'].search([('name', '=', 'Big Frozen Food POS')], limit=1)
        assert pos_config, "POS config not found!"

        # Close any active open/opening session so pos_config can be modified
        open_sessions = env['pos.session'].search([('config_id', '=', pos_config.id), ('state', '!=', 'closed')])
        for s in open_sessions:
            if s.state == 'opened':
                s.action_pos_session_closing_control()
            s.unlink()

        # Get or Create Journals
        cash_journal = env['account.journal'].search([('type', '=', 'cash'), ('name', '=', 'Cash BFF')], limit=1)
        if not cash_journal:
            cash_journal = env['account.journal'].create({
                'name': 'Cash BFF',
                'type': 'cash',
                'code': 'CSHB',
            })

        bank_journal = env['account.journal'].search([('type', '=', 'bank')], limit=1)
        if not bank_journal:
            bank_journal = env['account.journal'].create({
                'name': 'Bank BFF',
                'type': 'bank',
                'code': 'BNKB',
            })

        # Ensure Payment Methods exist specifically for this POS
        pm_cash = env['pos.payment.method'].search([('name', '=', 'Cash (BFF)')], limit=1)
        if not pm_cash:
            pm_cash = env['pos.payment.method'].create({'name': 'Cash (BFF)', 'journal_id': cash_journal.id})

        pm_transfer = env['pos.payment.method'].search([('name', '=', 'Bank Transfer (BFF)')], limit=1)
        if not pm_transfer:
            pm_transfer = env['pos.payment.method'].create({'name': 'Bank Transfer (BFF)', 'journal_id': bank_journal.id})

        pm_qris = env['pos.payment.method'].search([('name', '=', 'QRIS (BFF)')], limit=1)
        if not pm_qris:
            pm_qris = env['pos.payment.method'].create({'name': 'QRIS (BFF)', 'journal_id': bank_journal.id})

        pos_config.write({
            'payment_method_ids': [(6, 0, [pm_cash.id, pm_transfer.id, pm_qris.id])],
        })

        # Create & Open Session
        session = env['pos.session'].create({
            'config_id': pos_config.id,
            'user_id': SUPERUSER_ID,
        })
        session.action_pos_session_open()
        print(f" POS Session active: {session.name} (ID: {session.id})")

        # Partners & Products
        partner_umum = env['res.partner'].search([('name', '=', 'Pembeli Umum')], limit=1)
        partner_reseller = env['res.partner'].search([('name', '=', 'Reseller Frozen Pasuruan')], limit=1)
        partner_agen = env['res.partner'].search([('name', '=', 'Agen Frozen Food Pasuruan')], limit=1)

        p_nugget = env['product.product'].search([('name', '=', 'Nugget Ayam Original 500g')], limit=1)
        p_sosis = env['product.product'].search([('name', '=', 'Sosis Ayam 500g')], limit=1)
        p_fries = env['product.product'].search([('name', '=', 'French Fries Shoestring 1kg')], limit=1)
        p_fish = env['product.product'].search([('name', '=', 'Fish Roll 500g')], limit=1)

        # Transaction 1: Pembeli Umum (Cash, Public Price)
        # Nugget 2 pcs (35k), Sosis 2 pcs (30k), Fries 1 pc (32k) -> Total = 162k
        lines1 = [
            (0, 0, {'product_id': p_nugget.id, 'qty': 2, 'price_unit': 35000, 'price_subtotal': 70000, 'price_subtotal_incl': 70000}),
            (0, 0, {'product_id': p_sosis.id, 'qty': 2, 'price_unit': 30000, 'price_subtotal': 60000, 'price_subtotal_incl': 60000}),
            (0, 0, {'product_id': p_fries.id, 'qty': 1, 'price_unit': 32000, 'price_subtotal': 32000, 'price_subtotal_incl': 32000}),
        ]
        order1 = env['pos.order'].create({
            'session_id': session.id,
            'partner_id': partner_umum.id,
            'lines': lines1,
            'amount_total': 162000,
            'amount_tax': 0,
            'amount_paid': 162000,
            'amount_return': 0,
            'payment_ids': [(0, 0, {
                'payment_method_id': pm_cash.id,
                'amount': 162000,
            })],
        })
        order1.action_pos_order_paid()
        order1._create_order_picking()
        print(f" Transaction 1 (Pembeli Umum): Order {order1.name} paid Rp 162,000 via Cash.")

        # Transaction 2: Reseller (Bank Transfer, Reseller Price)
        # Nugget 20 pcs (32k = 640k), Sosis 20 pcs (27.5k = 550k), Fish Roll 10 pcs (25k = 250k) -> Total = 1,440,000
        lines2 = [
            (0, 0, {'product_id': p_nugget.id, 'qty': 20, 'price_unit': 32000, 'price_subtotal': 640000, 'price_subtotal_incl': 640000}),
            (0, 0, {'product_id': p_sosis.id, 'qty': 20, 'price_unit': 27500, 'price_subtotal': 550000, 'price_subtotal_incl': 550000}),
            (0, 0, {'product_id': p_fish.id, 'qty': 10, 'price_unit': 25000, 'price_subtotal': 250000, 'price_subtotal_incl': 250000}),
        ]
        order2 = env['pos.order'].create({
            'session_id': session.id,
            'partner_id': partner_reseller.id,
            'lines': lines2,
            'amount_total': 1440000,
            'amount_tax': 0,
            'amount_paid': 1440000,
            'amount_return': 0,
            'payment_ids': [(0, 0, {
                'payment_method_id': pm_transfer.id,
                'amount': 1440000,
            })],
        })
        order2.action_pos_order_paid()
        order2._create_order_picking()
        print(f" Transaction 2 (Reseller Pasuruan): Order {order2.name} paid Rp 1,440,000 via Bank Transfer.")

        # Transaction 3: Agen (QRIS, Agen Price)
        # Nugget 50 pcs (29k = 1,450k), Sosis 50 pcs (25k = 1,250k), Fries 30 pcs (26k = 780k) -> Total = 3,480,000
        lines3 = [
            (0, 0, {'product_id': p_nugget.id, 'qty': 50, 'price_unit': 29000, 'price_subtotal': 1450000, 'price_subtotal_incl': 1450000}),
            (0, 0, {'product_id': p_sosis.id, 'qty': 50, 'price_unit': 25000, 'price_subtotal': 1250000, 'price_subtotal_incl': 1250000}),
            (0, 0, {'product_id': p_fries.id, 'qty': 30, 'price_unit': 26000, 'price_subtotal': 780000, 'price_subtotal_incl': 780000}),
        ]
        order3 = env['pos.order'].create({
            'session_id': session.id,
            'partner_id': partner_agen.id,
            'lines': lines3,
            'amount_total': 3480000,
            'amount_tax': 0,
            'amount_paid': 3480000,
            'amount_return': 0,
            'payment_ids': [(0, 0, {
                'payment_method_id': pm_qris.id,
                'amount': 3480000,
            })],
        })
        order3.action_pos_order_paid()
        order3._create_order_picking()
        print(f" Transaction 3 (Agen Pasuruan): Order {order3.name} paid Rp 3,480,000 via QRIS.")

        session.action_pos_session_closing_control()

        cr.commit()
        print("=== POS DEMO TRANSACTIONS COMPLETED CLEANLY ===")

if __name__ == '__main__':
    run()
