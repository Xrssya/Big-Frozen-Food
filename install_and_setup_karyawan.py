#!/usr/bin/env python3
import sys

sys.path.insert(0, '/home/setyo/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'bigfrozenfood_db'
CONF_PATH = '/home/setyo/developer/odoo/odoo-BigFrozenFood/big_frozen_food.conf'

def setup():
    print("=========================================================")
    print("  UPGRADING BFF_KARYAWAN MODULE & 4 OFFICIAL ROLES")
    print("=========================================================")

    odoo.tools.config.parse_config(['-c', CONF_PATH, '-d', DB_NAME, '-u', 'hr,bff_karyawan'])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print(" -> Updating/Installing modules hr, bff_karyawan...")
        env['ir.module.module'].update_list()
        modules_to_install = env['ir.module.module'].search([('name', 'in', ['hr', 'bff_karyawan'])])
        modules_to_install.button_immediate_install()
        cr.commit()

    print(" -> Modules installed successfully!")

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        company = env['res.company'].search([('name', '=', 'Big Frozen Food')], limit=1)
        if not company:
            company = env['res.company'].search([], limit=1)

        print(f" -> Setting up employees for company: {company.name}")

        warehouse = env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)

        dep_kasir = env.ref('bff_karyawan.dep_kasir', raise_if_not_found=False)
        dep_gudang = env.ref('bff_karyawan.dep_gudang', raise_if_not_found=False)

        job_kasir = env.ref('bff_karyawan.job_kasir', raise_if_not_found=False)
        job_head_gudang = env.ref('bff_karyawan.job_head_gudang', raise_if_not_found=False)

        g_kepala_toko = env.ref('bff_karyawan.group_bff_kepala_toko')
        g_asisten_kepala_toko = env.ref('bff_karyawan.group_bff_asisten_kepala_toko')
        g_cashier = env.ref('bff_karyawan.group_bff_cashier')
        g_gudang = env.ref('bff_karyawan.group_bff_kepala_gudang')

        # 1. Kepala Toko (Admin)
        admin_user = env['res.users'].search([('login', '=', 'admin')], limit=1)
        if admin_user:
            admin_user.write({'groups_id': [(4, g_kepala_toko.id)]})
            emp_admin = env['hr.employee'].search([('user_id', '=', admin_user.id)], limit=1)
            if not emp_admin:
                emp_admin = env['hr.employee'].create({
                    'name': 'Kepala Toko (Administrator)',
                    'user_id': admin_user.id,
                    'job_title': 'Kepala Toko Utama',
                    'bff_role': 'kepala_toko',
                    'company_id': company.id,
                })
            else:
                emp_admin.write({'bff_role': 'kepala_toko'})
            print(" -> Configured Kepala Toko: Admin")

        # 2. Asisten Kepala Toko
        user_asisten = env['res.users'].search([('login', '=', 'asisten')], limit=1)
        if not user_asisten:
            user_asisten = env['res.users'].create({
                'name': 'Dewi Lestari (Asisten Kepala Toko)',
                'login': 'asisten',
                'password': 'asistenpassword123',
                'company_id': company.id,
                'company_ids': [(6, 0, [company.id])],
                'groups_id': [(6, 0, [
                    env.ref('base.group_user').id,
                    g_asisten_kepala_toko.id,
                ])],
            })
            print(" -> Created User Asisten Kepala Toko: asisten")

        emp_asisten = env['hr.employee'].search([('user_id', '=', user_asisten.id)], limit=1)
        if not emp_asisten:
            emp_asisten = env['hr.employee'].create({
                'name': 'Dewi Lestari',
                'user_id': user_asisten.id,
                'job_title': 'Asisten Kepala Toko',
                'bff_role': 'asisten_kepala_toko',
                'shift_schedule': 'full',
                'work_phone': '0811-7788-9900',
                'work_email': 'asisten.dewi@bigfrozenfood.com',
                'company_id': company.id,
                'warehouse_responsibilities': 'Supervisi harian toko, penanggung jawab operasional saat Kepala Toko absensi, dan kontrol stok.',
            })
            print(" -> Created Employee Asisten Kepala Toko: Dewi Lestari")
        else:
            emp_asisten.write({'bff_role': 'asisten_kepala_toko'})

        # 3. Kasir
        user_kasir = env['res.users'].search([('login', '=', 'kasir')], limit=1)
        if not user_kasir:
            user_kasir = env['res.users'].create({
                'name': 'Siti Rahma (Kasir)',
                'login': 'kasir',
                'password': 'kasirpassword123',
                'company_id': company.id,
                'company_ids': [(6, 0, [company.id])],
                'groups_id': [(6, 0, [
                    env.ref('base.group_user').id,
                    g_cashier.id,
                ])],
            })
            print(" -> Created User Kasir: kasir")
        else:
            user_kasir.write({'groups_id': [(4, g_cashier.id)]})

        emp_kasir = env['hr.employee'].search([('user_id', '=', user_kasir.id)], limit=1)
        if not emp_kasir:
            emp_kasir = env['hr.employee'].create({
                'name': 'Siti Rahma',
                'user_id': user_kasir.id,
                'department_id': dep_kasir.id if dep_kasir else False,
                'job_id': job_kasir.id if job_kasir else False,
                'job_title': 'Kasir Utama POS',
                'bff_role': 'kasir',
                'shift_schedule': 'morning',
                'work_phone': '0812-3456-7890',
                'work_email': 'kasir.siti@bigfrozenfood.com',
                'company_id': company.id,
                'warehouse_responsibilities': 'Penanggung jawab kasir POS, melayani transaksi tunai & non-tunai, mencetak struk thermal belanja pelanggan.',
            })
            print(" -> Created Employee Kasir: Siti Rahma")
        else:
            emp_kasir.write({'bff_role': 'kasir'})

        # 4. Kepala Gudang
        user_head_gudang = env['res.users'].search([('login', '=', 'head_gudang')], limit=1)
        if not user_head_gudang:
            user_head_gudang = env['res.users'].search([('login', '=', 'gudang')], limit=1)

        if not user_head_gudang:
            user_head_gudang = env['res.users'].create({
                'name': 'Agus Pratama (Kepala Gudang)',
                'login': 'head_gudang',
                'password': 'gudangpassword123',
                'company_id': company.id,
                'company_ids': [(6, 0, [company.id])],
                'groups_id': [(6, 0, [
                    env.ref('base.group_user').id,
                    g_gudang.id,
                ])],
            })
            print(" -> Created User Kepala Gudang: head_gudang")
        else:
            user_head_gudang.write({'groups_id': [(4, g_gudang.id)]})

        emp_head_gudang = env['hr.employee'].search([('user_id', '=', user_head_gudang.id)], limit=1)
        if not emp_head_gudang:
            emp_head_gudang = env['hr.employee'].create({
                'name': 'Agus Pratama',
                'user_id': user_head_gudang.id,
                'department_id': dep_gudang.id if dep_gudang else False,
                'job_id': job_head_gudang.id if job_head_gudang else False,
                'job_title': 'Kepala Gudang & Supervisor Stock',
                'bff_role': 'kepala_gudang',
                'shift_schedule': 'full',
                'assigned_warehouse_id': warehouse.id if warehouse else False,
                'work_phone': '0811-2233-4455',
                'work_email': 'head.gudang@bigfrozenfood.com',
                'company_id': company.id,
                'warehouse_responsibilities': 'Pengawasan total pendataan barang gudang, verifikasi stock opname berkala, penyusunan tata letak freezer, dan koordinasi pengiriman produk frozen food.',
            })
            print(" -> Created Employee Kepala Gudang: Agus Pratama")
        else:
            emp_head_gudang.write({'bff_role': 'kepala_gudang'})

        # Update all other employees with default mapping if needed
        all_emps = env['hr.employee'].search([])
        for emp in all_emps:
            if emp.bff_role == 'cashier':
                emp.write({'bff_role': 'kasir'})
            elif emp.bff_role in ['warehouse', 'manager']:
                emp.write({'bff_role': 'kepala_gudang' if emp.bff_role == 'warehouse' else 'kepala_toko'})
            emp._sync_user_groups()

        cr.commit()
        print("=========================================================")
        print(" 4 OFFICIAL ROLES INSTALLED AND CONFIGURED SUCCESSFULLY!")
        print("=========================================================")

if __name__ == '__main__':
    setup()
