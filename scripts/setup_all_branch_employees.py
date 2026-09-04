#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Karyawan Semua Cabang - Big Frozen Food
=============================================
Script ini membuat akun karyawan untuk semua cabang dengan ketentuan:
  - 3 Kasir per cabang
  - 2 Kepala Gudang per cabang
  - 4 Staf Gudang per cabang

Cara menjalankan:
  python3 setup_all_branch_employees.py
"""

import sys
import os
sys.path.insert(0, "/home/adi-purwanto/developer/odoo18")
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME   = 'odoo-big-frozen'
CONF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'big_frozen_food.conf')

KASIR_NAMES = [
    "Siti Rahma", "Dewi Puspita", "Rina Agustina", "Fitri Handayani", "Ayu Lestari",
    "Nita Permata", "Sari Wulandari", "Mega Rahayu", "Desi Kurniawati", "Lina Susanti",
    "Yuni Kartika", "Rini Maharani", "Vera Claudia", "Tika Amalia", "Putri Andini",
    "Nadia Saraswati", "Intan Permatasari", "Dian Anggraini", "Hani Pramesti", "Wati Nurhayati",
    "Eka Fitriani", "Asri Mulyani", "Sri Rahayu", "Nurul Hidayah", "Anisa Fatimah",
    "Ratih Kusuma", "Citra Dewi", "Mitha Oktavia", "Sisca Rahmawati", "Fani Rosdiana",
    "Ade Nuraini", "Bela Safitri", "Cici Noviyanti", "Dita Wibawati", "Ella Prasetya",
    "Fara Aulia", "Gita Supriyadi", "Hilda Rachmawati", "Ida Farida", "Jeni Lestari",
    "Kiki Amalia", "Lisa Noviyanti", "Mira Anggraeni", "Neni Susilowati", "Oki Permata",
    "Pita Sulsyati", "Qori Latifah", "Resa Oktaviani", "Sinta Nurbaya", "Tari Lestari",
]

KEPALA_GUDANG_NAMES = [
    "Agus Pratama", "Budi Santoso", "Chandra Wijaya", "Dedi Kurniawan", "Edi Susanto",
    "Fajar Nugroho", "Gunawan Prabowo", "Hendra Saputra", "Iwan Setiawan", "Joko Purnomo",
    "Karyadi Wibowo", "Lukman Hakim", "Mulyono Hadi", "Nanang Supriatna", "Oka Purwadi",
    "Purwanto Rasyid", "Rudi Hermawan", "Slamet Riyadi", "Taufik Hidayat", "Udin Sambodo",
    "Vino Kartawibawa", "Wahyu Prasetyo", "Yoyok Susilo", "Zaenal Arifin", "Arif Wicaksono",
    "Bambang Eko", "Catur Prasetyo", "Danu Setyawan", "Endar Kusuma", "Fauzan Maulana",
]

STAF_GUDANG_NAMES = [
    "Ahmad Fauzi", "Bachtiar Yusuf", "Cecep Supriadi", "Dadang Kurnia", "Eko Prasetyo",
    "Faisal Rahman", "Galih Pramudyo", "Hadi Santoso", "Imam Wahyudi", "Jajang Priyatna",
    "Koko Susanto", "Luthfi Ramadhani", "Maman Suparman", "Nanda Kusuma", "Ody Firmansyah",
    "Panji Satriya", "Rahmat Hidayah", "Sapto Wijoyo", "Teguh Santoso", "Umar Harahap",
    "Vian Nugraha", "Wahid Syahputra", "Yanto Sugiarto", "Zulham Nasution", "Andi Irawan",
    "Bagas Pratomo", "Cahyo Wibowo", "Dony Firmansah", "Efendi Lubis", "Fahrul Rozi",
    "Ginanjar Sukmana", "Haris Munandar", "Indra Gunawan", "Jefri Saragih", "Kurnia Alam",
    "Lukas Sirait", "Muhamad Ihsan", "Novri Setiadi", "Okta Nurhadi", "Pandu Suryadi",
    "Ridwan Maulana", "Septian Haryono", "Tino Kurniawan", "Ulum Syahri", "Vicky Hermawan",
    "Wendi Ramdan", "Yusuf Ananda", "Zikri Ramadhan", "Arie Wibowo", "Bimo Saputro",
]


def make_login_email(name, branch_code, role_prefix, idx_suffix=""):
    """Buat login dan email unik dari nama + cabang"""
    parts = name.lower().split()
    first = parts[0]
    last  = parts[-1] if len(parts) > 1 else ""
    slug  = f"{first}{last}" if last else first
    login = f"{role_prefix}.{slug}.{branch_code.lower()}{idx_suffix}"
    email = f"{slug}.{branch_code.lower()}@bigfrozenfood.com"
    return login, email


def create_user_if_needed(env, login, email, display_name, password, company, group_ids):
    user = env['res.users'].search([('login', '=', login)], limit=1)
    if not user:
        user = env['res.users'].sudo().create({
            'name': display_name,
            'login': login,
            'email': email,
            'password': password,
            'company_id': company.id,
            'company_ids': [(4, company.id)],
            'groups_id': [(6, 0, group_ids)],
        })
    return user


def setup_branch_employees(env, company, branch_code, kasir_offset, kepgud_offset, stafgud_offset):
    dep_kasir       = env.ref('bff_karyawan.dep_kasir',          raise_if_not_found=False)
    dep_gudang      = env.ref('bff_karyawan.dep_gudang',         raise_if_not_found=False)
    job_kasir       = env.ref('bff_karyawan.job_kasir',          raise_if_not_found=False)
    job_head_gudang = env.ref('bff_karyawan.job_head_gudang',    raise_if_not_found=False)
    job_staf_gudang = env.ref('bff_karyawan.job_staf_gudang',   raise_if_not_found=False)

    g_cashier   = env.ref('bff_karyawan.group_bff_cashier',       raise_if_not_found=False)
    g_kepgud    = env.ref('bff_karyawan.group_bff_kepala_gudang', raise_if_not_found=False)
    g_stafgud   = env.ref('bff_karyawan.group_bff_staf_gudang',  raise_if_not_found=False)
    g_base_user = env.ref('base.group_user')

    warehouse = env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
    created = {'kasir': 0, 'kepgud': 0, 'stafgud': 0}

    # ==== 3 KASIR ====
    shift_kasir = ['morning', 'afternoon', 'morning']
    for i in range(3):
        name = KASIR_NAMES[(kasir_offset + i) % len(KASIR_NAMES)]
        suffix = str(i + 1) if i > 0 else ""
        login, email = make_login_email(name, branch_code, 'kasir', suffix)
        gids = [g_base_user.id]
        if g_cashier:
            gids.append(g_cashier.id)
        user = create_user_if_needed(env, login, email, f"{name}", 'kasir123bff', company, gids)

        emp = env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not emp:
            env['hr.employee'].create({
                'name': name,
                'user_id': user.id,
                'department_id': dep_kasir.id if dep_kasir else False,
                'job_id': job_kasir.id if job_kasir else False,
                'job_title': f'Kasir POS – {branch_code}',
                'bff_role': 'kasir',
                'shift_schedule': shift_kasir[i],
                'work_email': email,
                'company_id': company.id,
                'account_password': 'kasir123bff',
                'warehouse_responsibilities': 'Melayani transaksi POS, pembayaran tunai & non-tunai, mencetak struk belanja pelanggan.',
            })
            created['kasir'] += 1

    # ==== 2 KEPALA GUDANG ====
    for i in range(2):
        name = KEPALA_GUDANG_NAMES[(kepgud_offset + i) % len(KEPALA_GUDANG_NAMES)]
        suffix = str(i + 1) if i > 0 else ""
        login, email = make_login_email(name, branch_code, 'kepgud', suffix)
        gids = [g_base_user.id]
        if g_kepgud:
            gids.append(g_kepgud.id)
        user = create_user_if_needed(env, login, email, f"{name}", 'gudang123bff', company, gids)

        emp = env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not emp:
            env['hr.employee'].create({
                'name': name,
                'user_id': user.id,
                'department_id': dep_gudang.id if dep_gudang else False,
                'job_id': job_head_gudang.id if job_head_gudang else False,
                'job_title': f'Kepala Gudang – {branch_code}',
                'bff_role': 'kepala_gudang',
                'shift_schedule': 'full',
                'work_email': email,
                'assigned_warehouse_id': warehouse.id if warehouse else False,
                'company_id': company.id,
                'account_password': 'gudang123bff',
                'warehouse_responsibilities': 'Supervisi gudang, verifikasi stock opname, koordinasi penerimaan barang dari supplier.',
            })
            created['kepgud'] += 1

    # ==== 4 STAF GUDANG ====
    shift_staf = ['morning', 'afternoon', 'morning', 'afternoon']
    for i in range(4):
        name = STAF_GUDANG_NAMES[(stafgud_offset + i) % len(STAF_GUDANG_NAMES)]
        suffix = str(i + 1) if i > 0 else ""
        login, email = make_login_email(name, branch_code, 'staf', suffix)
        gids = [g_base_user.id]
        if g_stafgud:
            gids.append(g_stafgud.id)
        user = create_user_if_needed(env, login, email, f"{name}", 'staf123bff', company, gids)

        emp = env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not emp:
            env['hr.employee'].create({
                'name': name,
                'user_id': user.id,
                'department_id': dep_gudang.id if dep_gudang else False,
                'job_id': job_staf_gudang.id if job_staf_gudang else False,
                'job_title': f'Staf Gudang – {branch_code}',
                'bff_role': 'staf_gudang',
                'shift_schedule': shift_staf[i],
                'work_email': email,
                'assigned_warehouse_id': warehouse.id if warehouse else False,
                'company_id': company.id,
                'account_password': 'staf123bff',
                'warehouse_responsibilities': 'Pengelolaan stok fisik, penerimaan barang, pencatatan expired date, penataan freezer.',
            })
            created['stafgud'] += 1

    return created


def main():
    print("=" * 65)
    print("  SETUP KARYAWAN SEMUA CABANG – BIG FROZEN FOOD")
    print("=" * 65)

    odoo.tools.config.parse_config(['-c', CONF_PATH, '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        main_company = env['res.company'].search([('name', '=', 'Big Frozen Food')], limit=1)
        if not main_company:
            main_company = env['res.company'].search([('parent_id', '=', False)], limit=1)

        branches = env['res.company'].search(
            [('parent_id', '=', main_company.id)], order='name asc'
        )

        if not branches:
            print("ERROR: Tidak ditemukan cabang! Jalankan dulu create_city_branches.py")
            return

        print(f"Ditemukan {len(branches)} cabang. Mulai membuat karyawan...\n")

        total_kasir   = 0
        total_kepgud  = 0
        total_stafgud = 0

        for idx, branch in enumerate(branches):
            branch_code = branch.name.split('-')[-1].strip() if '-' in branch.name else branch.name[:3].upper()
            # Bersihkan spasi dari kode cabang
            branch_code = branch_code.replace(' ', '')

            print(f"[{idx+1:02d}/{len(branches)}] {branch.name} ({branch_code})", end=" ... ")

            created = setup_branch_employees(
                env, branch, branch_code,
                kasir_offset=idx * 3,
                kepgud_offset=idx * 2,
                stafgud_offset=idx * 4,
            )

            print(f"Kasir+{created['kasir']} | KepGud+{created['kepgud']} | StafGud+{created['stafgud']}")

            total_kasir   += created['kasir']
            total_kepgud  += created['kepgud']
            total_stafgud += created['stafgud']

        cr.commit()

    print("\n" + "=" * 65)
    print("  SELESAI! Ringkasan Total Karyawan Baru:")
    print(f"  Kasir baru         : {total_kasir}")
    print(f"  Kepala Gudang baru : {total_kepgud}")
    print(f"  Staf Gudang baru   : {total_stafgud}")
    print(f"  TOTAL baru         : {total_kasir + total_kepgud + total_stafgud}")
    print("=" * 65)
    print("\nCredential Default Login:")
    print("  Kasir         — Password : kasir123bff")
    print("  Kepala Gudang — Password : gudang123bff")
    print("  Staf Gudang   — Password : staf123bff")
    print("\nFormat Login Username:")
    print("  kasir.{namadepannama}.{kodecabang}")
    print("  Contoh: kasir.sitirahma.sby | kepgud.aguspratama.mlg | staf.ahmadfauzi.jkt")


if __name__ == '__main__':
    main()
