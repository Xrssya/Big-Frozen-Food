#!/usr/bin/env python3
import sys

sys.path.insert(0, '/home/setyo/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'bigfrozenfood_db'
CONF_PATH = '/home/setyo/developer/odoo/odoo-BigFrozenFood/big_frozen_food.conf'

def verify():
    odoo.tools.config.parse_config(['-c', CONF_PATH, '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print("=== VERIFYING 4 OFFICIAL ROLES (KEPALA TOKO, ASISTEN, KASIR, KEPALA GUDANG) ===")

        # 1. Verify installed modules
        hr_mod = env['ir.module.module'].search([('name', '=', 'hr'), ('state', '=', 'installed')])
        bff_mod = env['ir.module.module'].search([('name', '=', 'bff_karyawan'), ('state', '=', 'installed')])
        assert hr_mod and bff_mod, "Modules hr / bff_karyawan missing!"
        print(" [PASS] Modules Installed: hr & bff_karyawan")

        # 2. Verify 4 security groups
        g_kt = env.ref('bff_karyawan.group_bff_kepala_toko', raise_if_not_found=False)
        g_akt = env.ref('bff_karyawan.group_bff_asisten_kepala_toko', raise_if_not_found=False)
        g_ks = env.ref('bff_karyawan.group_bff_cashier', raise_if_not_found=False)
        g_kg = env.ref('bff_karyawan.group_bff_kepala_gudang', raise_if_not_found=False)

        assert g_kt and g_akt and g_ks and g_kg, "One of the 4 security groups is missing!"
        print(f" [PASS] 4 Security Groups verified: '{g_kt.name}', '{g_akt.name}', '{g_ks.name}', '{g_kg.name}'")

        # 3. Verify Employees & User roles
        emp_kt = env['hr.employee'].search([('bff_role', 'in', ['kepala_toko', 'manager'])], limit=1)
        assert emp_kt, "Kepala Toko employee missing!"
        print(f" [PASS] Kepala Toko: {emp_kt.name} | Role: {emp_kt.bff_role}")

        emp_akt = env['hr.employee'].search([('bff_role', '=', 'asisten_kepala_toko')], limit=1)
        assert emp_akt, "Asisten Kepala Toko employee missing!"
        print(f" [PASS] Asisten Kepala Toko: {emp_akt.name} | Role: {emp_akt.bff_role}")

        emp_ks = env['hr.employee'].search([('bff_role', 'in', ['kasir', 'cashier'])], limit=1)
        assert emp_ks, "Kasir employee missing!"
        print(f" [PASS] Kasir: {emp_ks.name} | Role: {emp_ks.bff_role}")

        emp_kg = env['hr.employee'].search([('bff_role', 'in', ['kepala_gudang', 'warehouse'])], limit=1)
        assert emp_kg, "Kepala Gudang employee missing!"
        print(f" [PASS] Kepala Gudang: {emp_kg.name} | Role: {emp_kg.bff_role}")

        # 4. Verify group permissions match requested specification
        # Asisten Kepala Toko has same implied_ids as Kepala Toko
        kt_group_ids = set(g_kt.implied_ids.ids)
        akt_group_ids = set(g_akt.implied_ids.ids)
        assert kt_group_ids == akt_group_ids, "Asisten Kepala Toko permissions do not match Kepala Toko!"
        print(" [PASS] Verified: Asisten Kepala Toko permissions match Kepala Toko 100%")

        print("=== ALL 4 OFFICIAL ROLES VERIFIED SUCCESSFULLY ===")

if __name__ == '__main__':
    verify()
