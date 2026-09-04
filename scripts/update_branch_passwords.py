#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update Password Karyawan Semua Cabang - Big Frozen Food
Format baru:
  Kasir         -> Kasir{NamaKota}   misal: KasirBandung
  Kepala Gudang -> KG{NamaKota}      misal: KGBandung
  Staf Gudang   -> SG{NamaKota}      misal: SGBandung
"""
import sys, os
sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME   = 'odoo-big-frozen'
CONF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'big_frozen_food.conf')

# Map kode cabang di email -> nama kota bersih
CODE_TO_CITY = {
    'bdg': 'Bandung', 'bali': 'BadungBali', 'bdl': 'Binjai', 'bgr': 'Bogor',
    'bks': 'Bekasi', 'blt': 'Blitar', 'bnt': 'Bantul', 'btm': 'Batam',
    'bwi': 'Banyuwangi', 'cmh': 'Cimahi', 'crb': 'Cirebon', 'dpk': 'Depok',
    'dps': 'Denpasar', 'gny': 'Gianyar', 'grt': 'Garut', 'gsk': 'Gresik',
    'jbr': 'Jember', 'jkt': 'Jakarta', 'kdr': 'Kediri', 'kds': 'Kudus',
    'kwg': 'Karawang', 'lmj': 'Lumajang', 'mdn': 'Madiun', 'su': 'MedanSumut',
    'mgl': 'Magelang', 'mjk': 'Mojokerto', 'mlg': 'Malang', 'pkl': 'Pekalongan',
    'pku': 'Pekanbaru', 'plb': 'Palembang', 'prb': 'Probolinggo', 'psr': 'Pasuruan',
    'pwk': 'Purwokerto', 'pwt': 'Purwakarta', 'sby': 'Surabaya', 'sda': 'Sidoarjo',
    'skb': 'Sukabumi', 'slm': 'Sleman', 'slo': 'Solo', 'slt': 'Salatiga',
    'smg': 'Semarang', 'tab': 'Tabanan', 'tbn': 'Tuban', 'tgl': 'Tegal',
    'tgr': 'Tangerang', 'tsk': 'Tasikmalaya', 'ygy': 'Yogyakarta',
}

def get_city_from_email(email):
    """Ambil kode kota dari email: {nama}.{kotakode}@bigfrozenfood.com"""
    local = email.split('@')[0]          # misal: aguspratama.bdg
    parts = local.split('.')
    if len(parts) >= 2:
        code = parts[-1].lower()         # ambil bagian terakhir = kode kota
        return CODE_TO_CITY.get(code, code.capitalize())
    return None

def main():
    print("=" * 65)
    print("  UPDATE PASSWORD KARYAWAN - BIG FROZEN FOOD")
    print("=" * 65)

    odoo.tools.config.parse_config(['-c', CONF_PATH, '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Ambil semua employee yang punya user_id dan bff_role
        employees = env['hr.employee'].search([
            ('user_id', '!=', False),
            ('bff_role', 'in', ['kasir', 'kepala_gudang', 'staf_gudang']),
        ])

        print(f"Ditemukan {len(employees)} karyawan dengan role kasir/kepala_gudang/staf_gudang\n")

        updated = 0
        skipped = 0
        errors  = 0

        for emp in employees:
            user = emp.user_id
            email = user.login  # login = email

            city = get_city_from_email(email)
            if not city:
                skipped += 1
                continue

            # Tentukan format password berdasarkan role
            if emp.bff_role == 'kasir':
                new_pw = f"Kasir{city}"
            elif emp.bff_role == 'kepala_gudang':
                new_pw = f"KG{city}"
            elif emp.bff_role == 'staf_gudang':
                new_pw = f"SG{city}"
            else:
                skipped += 1
                continue

            try:
                user.sudo().write({'password': new_pw})
                emp.sudo().write({'account_password': new_pw})
                updated += 1
                if updated <= 5 or updated % 50 == 0:
                    print(f"  [{updated}] {emp.name} ({emp.bff_role}) -> pw: {new_pw}")
            except Exception as e:
                print(f"  ERROR {user.login}: {e}")
                errors += 1

        cr.commit()

    print()
    print("=" * 65)
    print(f"  SELESAI!")
    print(f"  Password diupdate : {updated}")
    print(f"  Dilewati          : {skipped}")
    print(f"  Error             : {errors}")
    print("=" * 65)
    print()
    print("Contoh password:")
    print("  Kasir Bandung         -> KasirBandung")
    print("  Kepala Gudang Surabaya-> KGSurabaya")
    print("  Staf Gudang Jakarta   -> SGJakarta")

if __name__ == '__main__':
    main()
