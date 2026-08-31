# -*- coding: utf-8 -*-
import sys
import os
import random

import odoo
from odoo import api, SUPERUSER_ID

def run_create_outlets(db_name):
    print(f"\n=======================================================")
    print(f"  CREATING STREET-LEVEL STORE OUTLETS FOR DB: {db_name}")
    print(f"=======================================================")
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'big_frozen_food.conf')
    odoo.tools.config.parse_config(['-c', config_file, '-d', db_name])
    registry = odoo.registry(db_name)

    # Street names dictionary for cities
    city_streets = {
        'SBY': [
            'Jl. Ahmad Yani No. 120 (Gayungan)',
            'Jl. HR Muhammad No. 45 (Surabaya Barat)',
            'Jl. MERR Rungkut No. 88 (Surabaya Timur)',
            'Jl. Dharmahusada No. 15 (Gubeng)',
            'Jl. Mayjen Sungkono No. 202 (Sawahan)',
        ],
        'MLG': [
            'Jl. Soekarno Hatta No. 9 (Lowokwaru)',
            'Jl. Besar Ijen No. 42 (Klojen)',
            'Jl. Veteran No. 18 (Sumbersari)',
        ],
        'SDA': [
            'Jl. Pahlawan No. 50 (Sidoarjo Kota)',
            'Jl. Gajah Mada No. 12 (Candi)',
            'Jl. Jenggolo No. 34 (Buduran)',
        ],
        'GSK': [
            'Jl. Veteran No. 88 (Kebomas)',
            'Jl. Dr. Wahidin No. 15 (Gresik Kota)',
        ],
        'JKT': [
            'Jl. Jend. Sudirman No. 45 (Jakarta Selatan)',
            'Jl. Kelapa Gading Boulevard No. 18 (Jakarta Utara)',
            'Jl. Puri Indah Raya No. 8 (Jakarta Barat)',
            'Jl. Tebet Raya No. 55 (Jakarta Selatan)',
        ],
        'SMG': [
            'Jl. Pandanaran No. 60 (Semarang Tengah)',
            'Jl. Pemuda No. 101 (Semarang Barat)',
            'Jl. Gajah Mada No. 25 (Semarang Selatan)',
        ],
        'SLO': [
            'Jl. Slamet Riyadi No. 150 (Laweyan)',
            'Jl. Veteran No. 77 (Pasar Kliwon)',
        ],
        'YGY': [
            'Jl. Malioboro No. 30 (Gedongtengen)',
            'Jl. Kaliurang Km 5 (Depok Sleman)',
            'Jl. Gejayan No. 12 (Caturtunggal)',
        ],
        'BDG': [
            'Jl. Riau / RE Martadinata No. 85 (Bandung Wetan)',
            'Jl. Ir. H. Juanda / Dago No. 110 (Coblong)',
            'Jl. Buah Batu No. 140 (Lengkong)',
        ],
        'DPS': [
            'Jl. Sunset Road No. 88 (Kuta)',
            'Jl. Teuku Umar No. 120 (Denpasar Barat)',
            'Jl. Gatot Subroto No. 45 (Denpasar Utara)',
        ],
        'BGR': [
            'Jl. Pajajaran No. 33 (Bogor Timur)',
            'Jl. Raya Juanda No. 12 (Bogor Tengah)',
        ],
        'BKS': [
            'Jl. Ahmad Yani No. 88 (Bekasi Selatan)',
            'Jl. Harapan Indah Boulevard No. 15 (Tarumajaya)',
        ],
        'TGR': [
            'Jl. BSD Grand Boulevard No. 9 (Serpong)',
            'Jl. Daan Mogot No. 55 (Tangerang Kota)',
        ],
        'DPK': [
            'Jl. Margonda Raya No. 150 (Beji)',
            'Jl. Raya Sawangan No. 42 (Pancasaran)',
        ],
        'CRB': [
            'Jl. Kartini No. 25 (Kejaksan)',
            'Jl. Siliwangi No. 88 (Lemahwungkuk)',
        ],
        'JBR': [
            'Jl. Gajah Mada No. 90 (Kaliwates)',
            'Jl. Kalimantan No. 15 (Sumbersari)',
        ],
        'KDR': [
            'Jl. Dhoho No. 45 (Kota Kediri)',
            'Jl. Brawijaya No. 12 (Pesantren)',
        ],
        'BWI': [
            'Jl. Ahmad Yani No. 66 (Banyuwangi Kota)',
            'Jl. Gajah Mada No. 10 (Giri)',
        ],
        'MDN-SU': [
            'Jl. Gatot Subroto No. 120 (Medan Petisah)',
            'Jl. S. Parman No. 45 (Medan Baru)',
        ],
        'PLB': [
            'Jl. Jend. Sudirman No. 88 (Palembang Kota)',
            'Jl. Angkatan 45 No. 20 (Ilir Barat)',
        ],
        'PKU': [
            'Jl. Jend. Sudirman No. 150 (Pekanbaru Kota)',
            'Jl. Tuanku Tambusai No. 88 (Marpoyan)',
        ],
    }

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        companies = env['res.company'].search([('name', 'like', 'Big Frozen Food - %')])
        print(f"Found {len(companies)} branch companies.")

        total_new_configs = 0
        total_reallocated_orders = 0

        for comp in companies:
            # Determine city code from company name e.g. 'Big Frozen Food - SBY' -> 'SBY'
            code = comp.name.split('-')[-1].strip()
            streets = city_streets.get(code, [f"Jl. Utama No. {random.randint(1, 99)} ({comp.city or 'Pusat'})", f"Jl. Pemuda No. {random.randint(1, 99)} ({comp.city or 'Cabang'})"])

            # Find or create sale journal for company
            sale_journal = env['account.journal'].search([
                ('company_id', '=', comp.id),
                ('type', '=', 'sale')
            ], limit=1)
            if not sale_journal:
                sale_journal = env['account.journal'].create({
                    'name': f"Penjualan POS {comp.city or code}",
                    'code': f"P{code[:4].upper()}",
                    'type': 'sale',
                    'company_id': comp.id
                })

            # Get payment methods for company
            pay_methods = env['pos.payment.method'].search([('company_id', '=', comp.id)])
            non_cash_methods = pay_methods.filtered(lambda m: m.journal_id.type != 'cash')

            # Existing configs for this company
            existing_configs = env['pos.config'].search([('company_id', '=', comp.id)])
            created_configs = list(existing_configs)

            # Update existing config name if it's generic e.g. "POS Kasir Big Frozen Food - SBY"
            if existing_configs:
                first_cfg = existing_configs[0]
                first_street = streets[0]
                new_name = f"Toko {code} - {first_street}"
                first_cfg.write({'name': new_name})
                print(f"Renamed primary config for {comp.name} -> {new_name}")

            # Create remaining street-level configs for this city
            for idx, street in enumerate(streets[1:], start=2):
                config_name = f"Toko {code} - {street}"
                cfg = env['pos.config'].search([('company_id', '=', comp.id), ('name', '=', config_name)], limit=1)
                if not cfg:
                    cfg_pay_methods = list(non_cash_methods.ids)

                    # Cash payment method needs its OWN unique cash journal per company
                    cash_journal_code = f"CS{idx:02d}"[:5]
                    cash_journal = env['account.journal'].search([
                        ('company_id', '=', comp.id),
                        ('code', '=', cash_journal_code)
                    ], limit=1)
                    if not cash_journal:
                        cash_journal = env['account.journal'].create({
                            'name': f"Kas {street}",
                            'code': cash_journal_code,
                            'type': 'cash',
                            'company_id': comp.id
                        })

                    cash_pm_name = f"Tunai - {street}"
                    cash_pm = env['pos.payment.method'].search([
                        ('company_id', '=', comp.id),
                        ('name', '=', cash_pm_name)
                    ], limit=1)
                    if not cash_pm:
                        cash_pm = env['pos.payment.method'].create({
                            'name': cash_pm_name,
                            'journal_id': cash_journal.id,
                            'company_id': comp.id
                        })
                    cfg_pay_methods.append(cash_pm.id)

                    cfg = env['pos.config'].create({
                        'name': config_name,
                        'company_id': comp.id,
                        'journal_id': sale_journal.id,
                        'invoice_journal_id': sale_journal.id,
                        'payment_method_ids': [(6, 0, cfg_pay_methods)]
                    })
                    total_new_configs += 1
                    print(f"  + Created outlet: {config_name}")
                created_configs.append(cfg)

            # Now create pos.session for each config
            created_sessions = []
            for cfg in created_configs:
                sess = env['pos.session'].search([('config_id', '=', cfg.id)], limit=1)
                if not sess:
                    sess = env['pos.session'].create({
                        'config_id': cfg.id,
                        'user_id': SUPERUSER_ID,
                    })
                    sess.action_pos_session_open()
                created_sessions.append(sess)

            # Reallocate/distribute existing pos.orders of this company across the street-level outlets
            company_orders = env['pos.order'].search([('company_id', '=', comp.id)])
            if company_orders:
                orders_list = list(company_orders)
                random.shuffle(orders_list)
                chunk_size = len(orders_list) // len(created_configs)
                
                for idx, cfg in enumerate(created_configs):
                    sess = created_sessions[idx]
                    start_i = idx * chunk_size
                    end_i = (idx + 1) * chunk_size if idx < len(created_configs) - 1 else len(orders_list)
                    target_orders = orders_list[start_i:end_i]
                    
                    for order in target_orders:
                        order.write({
                            'config_id': cfg.id,
                            'session_id': sess.id,
                        })
                        total_reallocated_orders += 1

                print(f"Reallocated {len(company_orders)} orders across {len(created_configs)} store outlets in {comp.name}")

        cr.commit()
        print(f"\nSUCCESS! Created {total_new_configs} new street-level store outlets.")
        print(f"Reallocated {total_reallocated_orders} transactions across all street outlets!")

def main():
    run_create_outlets('odoo-big-frozen')

if __name__ == '__main__':
    main()
