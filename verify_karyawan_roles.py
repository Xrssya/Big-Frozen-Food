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
        print("=== VERIFYING KARYAWAN MODULE & ROLES (KASIR & GUDANG) ===")

        # 1. Verify installed modules
        hr_mod = env['ir.module.module'].search([('name', '=', 'hr'), ('state', '=', 'installed')])
        bff_mod = env['ir.module.module'].search([('name', '=', 'bff_karyawan'), ('state', '=', 'installed')])
        assert hr_mod, "HR module is not installed!"
        assert bff_mod, "bff_karyawan module is not installed!"
        print(" [PASS] Modules Installed: hr (Karyawan) & bff_karyawan")

        # 2. Verify security groups
        group_cashier = env.ref('bff_karyawan.group_bff_cashier', raise_if_not_found=False)
        group_warehouse = env.ref('bff_karyawan.group_bff_warehouse', raise_if_not_found=False)
        assert group_cashier, "Group Kasir (group_bff_cashier) not found!"
        assert group_warehouse, "Group Staf Gudang (group_bff_warehouse) not found!"
        print(f" [PASS] Security Groups verified: '{group_cashier.name}' & '{group_warehouse.name}'")

        # 3. Verify Employees
        employees = env['hr.employee'].search([])
        print(f" [PASS] Total Employees in DB: {len(employees)}")

        emp_kasir = env['hr.employee'].search([('bff_role', '=', 'cashier')], limit=1)
        assert emp_kasir, "Employee with Role Kasir not found!"
        print(f" [PASS] Kasir Employee: {emp_kasir.name} | Job: {emp_kasir.job_id.name if emp_kasir.job_id else '-'} | User: {emp_kasir.user_id.login if emp_kasir.user_id else '-'}")

        emp_gudang = env['hr.employee'].search([('bff_role', '=', 'warehouse')], limit=1)
        assert emp_gudang, "Employee with Role Gudang not found!"
        print(f" [PASS] Warehouse Employee: {emp_gudang.name} | Job: {emp_gudang.job_id.name if emp_gudang.job_id else '-'} | Responsibilities: {emp_gudang.warehouse_responsibilities[:60]}...")

        # 4. Verify User Permissions & Roles
        user_kasir = env['res.users'].search([('login', '=', 'kasir')], limit=1)
        assert user_kasir and group_cashier in user_kasir.groups_id, "User kasir missing group_bff_cashier!"
        print(f" [PASS] User '{user_kasir.login}' has role Kasir & Point of Sale permissions")

        user_gudang = env['res.users'].search([('login', '=', 'gudang')], limit=1)
        assert user_gudang and group_warehouse in user_gudang.groups_id, "User gudang missing group_bff_warehouse!"
        print(f" [PASS] User '{user_gudang.login}' has role Staf Gudang & Inventory/Stock permissions")

        # 5. Verify Departments & Job Positions
        dep_kasir = env.ref('bff_karyawan.dep_kasir', raise_if_not_found=False)
        dep_gudang = env.ref('bff_karyawan.dep_gudang', raise_if_not_found=False)
        assert dep_kasir and dep_gudang, "Departments missing!"
        print(f" [PASS] Departments verified: '{dep_kasir.name}' and '{dep_gudang.name}'")

        print("=== ALL KARYAWAN & ROLE VERIFICATIONS PASSED SUCCESSFULLY ===")

if __name__ == '__main__':
    verify()
