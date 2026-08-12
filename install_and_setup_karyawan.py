#!/usr/bin/env python3
import sys

sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'odoo-big-frozen'
CONF_PATH = '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf'

def setup():
    print("=========================================================")
    print("  INSTALLING HR & BFF_KARYAWAN MODULES TO DB:", DB_NAME)
    print("=========================================================")

    # Parse config and update modules
    odoo.tools.config.parse_config(['-c', CONF_PATH, '-d', DB_NAME, '-i', 'hr,bff_karyawan'])
    
    # Perform module upgrade / install in registry
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print(" -> Updating/Installing modules hr, bff_karyawan...")
        env['ir.module.module'].update_list()
        modules_to_install = env['ir.module.module'].search([('name', 'in', ['hr', 'bff_karyawan'])])
        modules_to_install.button_immediate_install()
        cr.commit()

    print(" -> Modules installed successfully!")

    # Now populate data & verify
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
        job_staf_gudang = env.ref('bff_karyawan.job_staf_gudang', raise_if_not_found=False)
        job_head_gudang = env.ref('bff_karyawan.job_head_gudang', raise_if_not_found=False)

        group_cashier = env.ref('bff_karyawan.group_bff_cashier')
        group_warehouse = env.ref('bff_karyawan.group_bff_warehouse')

        # 1. User & Karyawan Kasir
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
                    group_cashier.id,
                    env.ref('point_of_sale.group_pos_user').id,
                ])],
            })
            print(" -> Created User Kasir: kasir")
        else:
            user_kasir.write({
                'groups_id': [(4, group_cashier.id), (4, env.ref('point_of_sale.group_pos_user').id)]
            })

        emp_kasir = env['hr.employee'].search([('user_id', '=', user_kasir.id)], limit=1)
        if not emp_kasir:
            emp_kasir = env['hr.employee'].create({
                'name': 'Siti Rahma',
                'user_id': user_kasir.id,
                'department_id': dep_kasir.id if dep_kasir else False,
                'job_id': job_kasir.id if job_kasir else False,
                'job_title': 'Kasir Utama POS',
                'bff_role': 'cashier',
                'shift_schedule': 'morning',
                'work_phone': '0812-3456-7890',
                'work_email': 'kasir.siti@bigfrozenfood.com',
                'company_id': company.id,
                'warehouse_responsibilities': 'Penanggung jawab kasir POS, melayani transaksi tunai & non-tunai, mencetak struk thermal belanja pelanggan.',
            })
            print(" -> Created Employee Kasir: Siti Rahma")

        # 2. User & Karyawan Orang Gudang (Staf Gudang)
        user_gudang = env['res.users'].search([('login', '=', 'gudang')], limit=1)
        if not user_gudang:
            user_gudang = env['res.users'].create({
                'name': 'Budi Santoso (Staf Gudang)',
                'login': 'gudang',
                'password': 'gudangpassword123',
                'company_id': company.id,
                'company_ids': [(6, 0, [company.id])],
                'groups_id': [(6, 0, [
                    env.ref('base.group_user').id,
                    group_warehouse.id,
                    env.ref('stock.group_stock_user').id,
                ])],
            })
            print(" -> Created User Gudang: gudang")
        else:
            user_gudang.write({
                'groups_id': [(4, group_warehouse.id), (4, env.ref('stock.group_stock_user').id)]
            })

        emp_gudang = env['hr.employee'].search([('user_id', '=', user_gudang.id)], limit=1)
        if not emp_gudang:
            emp_gudang = env['hr.employee'].create({
                'name': 'Budi Santoso',
                'user_id': user_gudang.id,
                'department_id': dep_gudang.id if dep_gudang else False,
                'job_id': job_staf_gudang.id if job_staf_gudang else False,
                'job_title': 'Staf Stock & Inventaris Gudang',
                'bff_role': 'warehouse',
                'shift_schedule': 'morning',
                'assigned_warehouse_id': warehouse.id if warehouse else False,
                'work_phone': '0813-9876-5432',
                'work_email': 'gudang.budi@bigfrozenfood.com',
                'company_id': company.id,
                'warehouse_responsibilities': 'Mendata seluruh barang di gudang frozen food, input penerimaan barang supplier, penataan barang di cold storage, dan pencatatan stock opname fisik.',
            })
            print(" -> Created Employee Gudang: Budi Santoso")

        # 3. User & Karyawan Kepala Gudang
        user_head_gudang = env['res.users'].search([('login', '=', 'head_gudang')], limit=1)
        if not user_head_gudang:
            user_head_gudang = env['res.users'].create({
                'name': 'Agus Pratama (Kepala Gudang)',
                'login': 'head_gudang',
                'password': 'gudangpassword123',
                'company_id': company.id,
                'company_ids': [(6, 0, [company.id])],
                'groups_id': [(6, 0, [
                    env.ref('base.group_user').id,
                    group_warehouse.id,
                    env.ref('stock.group_stock_manager').id,
                ])],
            })
            print(" -> Created User Head Gudang: head_gudang")

        emp_head_gudang = env['hr.employee'].search([('user_id', '=', user_head_gudang.id)], limit=1)
        if not emp_head_gudang:
            emp_head_gudang = env['hr.employee'].create({
                'name': 'Agus Pratama',
                'user_id': user_head_gudang.id,
                'department_id': dep_gudang.id if dep_gudang else False,
                'job_id': job_head_gudang.id if job_head_gudang else False,
                'job_title': 'Kepala Gudang & Supervisor Stock',
                'bff_role': 'warehouse',
                'shift_schedule': 'full',
                'assigned_warehouse_id': warehouse.id if warehouse else False,
                'work_phone': '0811-2233-4455',
                'work_email': 'head.gudang@bigfrozenfood.com',
                'company_id': company.id,
                'warehouse_responsibilities': 'Pengawasan total pendataan barang gudang, verifikasi stock opname berkala, penyusunan tata letak freezer, dan koordinasi pengiriman produk frozen food.',
            })
            print(" -> Created Employee Head Gudang: Agus Pratama")

        # 4. Give admin full access to new groups
        admin_user = env['res.users'].search([('login', '=', 'admin')], limit=1)
        if admin_user:
            admin_user.write({
                'groups_id': [(4, group_cashier.id), (4, group_warehouse.id)]
            })

        cr.commit()
        print("=========================================================")
        print("  SETUP AND INSTALATION COMPLETED SUCCESSFULLY!")
        print("=========================================================")

if __name__ == '__main__':
    setup()
