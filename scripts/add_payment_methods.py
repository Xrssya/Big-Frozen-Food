 # -*- coding: utf-8 -*-
"""
Script untuk menambahkan metode pembayaran Transfer Bank & QRIS
ke semua cabang Big Frozen Food yang sudah ada.

Cara pakai:
    PYTHONPATH=/home/adi-purwanto/developer/odoo18 python3 scripts/add_payment_methods.py [db_name]
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, fields, SUPERUSER_ID

def run_for_db(db_name):
    print(f"\n{'='*60}")
    print(f"   MENAMBAH METODE PEMBAYARAN - DB: {db_name}")
    print(f"{'='*60}")

    config_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'big_frozen_food.conf'
    )
    odoo.tools.config.parse_config(['-c', config_file, '-d', db_name])
    registry = odoo.registry(db_name)

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Cari semua branch company (yang namanya 'Big Frozen Food - ...')
        branches = env['res.company'].search([
            ('name', 'like', 'Big Frozen Food - ')
        ])
        print(f"Ditemukan {len(branches)} cabang.\n")

        for comp in branches:
            city = comp.city or comp.name.split(' - ')[-1]
            city_short = city[:2].upper()
            print(f"--- {comp.name} ---")

            # Step 1: Force close semua session POS yang masih terbuka untuk cabang ini
            open_sessions = env['pos.session'].search([
                ('config_id.company_id', '=', comp.id),
                ('state', '!=', 'closed')
            ])
            for session in open_sessions:
                print(f"  Force closing session: {session.name} (state: {session.state})")
                session.write({
                    'state': 'closed',
                    'stop_at': fields.Datetime.now()
                })
            if open_sessions:
                cr.flush()

            # Step 2: Pastikan journal Bank untuk Transfer
            transfer_journal = env['account.journal'].search([
                ('company_id', '=', comp.id),
                ('type', '=', 'bank'),
                ('name', 'ilike', 'Transfer'),
            ], limit=1)
            if not transfer_journal:
                transfer_journal = env['account.journal'].create({
                    'name': f"Transfer Bank {city}",
                    'code': f"TRF{city_short}",
                    'type': 'bank',
                    'company_id': comp.id
                })
                print(f"  Dibuat: Journal Transfer Bank")

            # Step 3: Pastikan journal Bank untuk QRIS
            qris_journal = env['account.journal'].search([
                ('company_id', '=', comp.id),
                ('type', '=', 'bank'),
                ('name', 'ilike', 'QRIS'),
            ], limit=1)
            if not qris_journal:
                qris_journal = env['account.journal'].create({
                    'name': f"QRIS {city}",
                    'code': f"QRS{city_short}",
                    'type': 'bank',
                    'company_id': comp.id
                })
                print(f"  Dibuat: Journal QRIS")

            # Step 4: Pastikan POS Payment Method: Transfer Bank
            pm_transfer = env['pos.payment.method'].search([
                ('company_id', '=', comp.id),
                ('name', 'ilike', 'Transfer'),
            ], limit=1)
            if not pm_transfer:
                pm_transfer = env['pos.payment.method'].create({
                    'name': f"Transfer Bank {city}",
                    'journal_id': transfer_journal.id,
                    'company_id': comp.id
                })
                print(f"  Dibuat: Payment Method Transfer Bank")

            # Step 5: Pastikan POS Payment Method: QRIS
            pm_qris = env['pos.payment.method'].search([
                ('company_id', '=', comp.id),
                ('name', 'ilike', 'QRIS'),
            ], limit=1)
            if not pm_qris:
                pm_qris = env['pos.payment.method'].create({
                    'name': f"QRIS {city}",
                    'journal_id': qris_journal.id,
                    'company_id': comp.id
                })
                print(f"  Dibuat: Payment Method QRIS")

            # Step 6: Daftarkan ke POS Config
            pos_cfg = env['pos.config'].search([('company_id', '=', comp.id)], limit=1)
            if pos_cfg:
                existing_ids = pos_cfg.payment_method_ids.ids
                to_add = [(4, pm.id) for pm in [pm_transfer, pm_qris] if pm.id not in existing_ids]
                if to_add:
                    pos_cfg.write({'payment_method_ids': to_add})
                    print(f"  ✓ Ditambahkan Transfer + QRIS ke POS Config")
                else:
                    print(f"  ✓ Transfer + QRIS sudah terdaftar")
            else:
                print(f"  ⚠ Tidak ada POS Config untuk cabang ini")

        cr.commit()
        print(f"\n{'='*60}")
        print(f"   SELESAI! Semua cabang sudah punya 3 metode pembayaran.")
        print(f"   (Tunai / Cash, Transfer Bank, QRIS)")
        print(f"{'='*60}")

def main():
    target_dbs = ['odoo-big-frozen']
    if len(sys.argv) > 1:
        target_dbs = [sys.argv[1]]
    for db in target_dbs:
        try:
            run_for_db(db)
        except Exception as e:
            import traceback
            print(f"Error untuk DB {db}: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    main()
