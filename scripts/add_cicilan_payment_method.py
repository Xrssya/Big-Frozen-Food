# -*- coding: utf-8 -*-
"""
Script untuk mengonfigurasi dan memasangkan metode pembayaran "Cicilan"
ke seluruh cabang POS Big Frozen Food yang ada di database.

Cara pakai:
    PYTHONPATH=/home/rsya/developer/odoo18 python3 scripts/add_cicilan_payment_method.py [db_name]
"""
import sys
import os

sys.path.insert(0, '/home/rsya/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

def run_for_db(db_name):
    print(f"\n{'='*60}")
    print(f"   MENAMBAH METODE PEMBAYARAN CICILAN - DB: {db_name}")
    print(f"{'='*60}")

    config_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'big_frozen_food.conf'
    )
    odoo.tools.config.parse_config(['-c', config_file, '-d', db_name])
    registry = odoo.registry(db_name)

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        companies = env['res.company'].search([])
        print(f"Ditemukan {len(companies)} company/cabang.\n")

        for comp in companies:
            print(f"--- {comp.name} ---")

            pm_cicilan = env['pos.payment.method'].search([
                ('company_id', '=', comp.id),
                ('name', 'ilike', 'Cicilan'),
            ], limit=1)

            if not pm_cicilan:
                pm_cicilan = env['pos.payment.method'].create({
                    'name': 'Cicilan',
                    'company_id': comp.id,
                    'is_cicilan': True,
                    'split_transactions': True,
                    'journal_id': False,
                })
                print(f"  ✓ Dibuat POS Payment Method 'Cicilan'")
            else:
                pm_cicilan.write({
                    'is_cicilan': True,
                })
                print(f"  ✓ Diperbarui POS Payment Method 'Cicilan'")

            pos_configs = env['pos.config'].search([('company_id', '=', comp.id)])
            for cfg in pos_configs:
                if pm_cicilan.id not in cfg.payment_method_ids.ids:
                    cfg.with_context(bypass_payment_method_ids_forbidden_change=True).write({
                        'payment_method_ids': [(4, pm_cicilan.id)]
                    })
                    print(f"  ✓ Ditambahkan 'Cicilan' ke POS Config: {cfg.name}")
                else:
                    print(f"  ✓ 'Cicilan' sudah ada di POS Config: {cfg.name}")

        cr.commit()
        print(f"\n{'='*60}")
        print(f"   SELESAI! Semua cabang sudah terkonfigurasi metode pembayaran Cicilan.")
        print(f"{'='*60}")

def main():
    target_dbs = ['odoo-big-frozen-food']
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
