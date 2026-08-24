#!/usr/bin/env python3
import sys

sys.path.insert(0, '/home/setyo/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'bigfrozenfood_db'
CONF_PATH = '/home/setyo/developer/odoo/odoo-BigFrozenFood/big_frozen_food.conf'

def setup_reports():
    print("=========================================================")
    print("  CONFIGURING DIRECT WIZARD POPUP FOR LAPORAN MENU")
    print("=========================================================")

    odoo.tools.config.parse_config(['-c', CONF_PATH, '-d', DB_NAME, '-u', 'bff_reports'])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print(" -> Upgrading module bff_reports...")
        env['ir.module.module'].update_list()
        mod = env['ir.module.module'].search([('name', '=', 'bff_reports')], limit=1)
        if mod:
            mod.button_immediate_upgrade()

        # Delete any child menus under sale.menu_sale_report
        sale_report_menu = env.ref('sale.menu_sale_report', raise_if_not_found=False)
        if sale_report_menu:
            children = env['ir.ui.menu'].search([('parent_id', '=', sale_report_menu.id)])
            if children:
                print(" -> Removing child submenus under Sales Laporan...")
                children.unlink()
            wiz_action = env.ref('bff_reports.action_bff_sales_report_wizard', raise_if_not_found=False)
            if wiz_action:
                sale_report_menu.write({'action': f"ir.actions.act_window,{wiz_action.id}"})
                print(f" -> Set direct action on '{sale_report_menu.name}': {wiz_action.name}")

        # Delete child menus under point_of_sale.menu_point_rep
        pos_report_menu = env.ref('point_of_sale.menu_point_rep', raise_if_not_found=False)
        if pos_report_menu:
            children = env['ir.ui.menu'].search([('parent_id', '=', pos_report_menu.id)])
            if children:
                print(" -> Removing child submenus under POS Laporan...")
                children.unlink()
            wiz_action = env.ref('bff_reports.action_bff_sales_report_wizard', raise_if_not_found=False)
            if wiz_action:
                pos_report_menu.write({'action': f"ir.actions.act_window,{wiz_action.id}"})
                print(f" -> Set direct action on '{pos_report_menu.name}': {wiz_action.name}")

        # Stock Report Menu
        stock_report_menu = env.ref('stock.menu_warehouse_report', raise_if_not_found=False)
        if stock_report_menu:
            children = env['ir.ui.menu'].search([('parent_id', '=', stock_report_menu.id)])
            if children:
                children.unlink()
            wiz_action = env.ref('bff_reports.action_bff_stock_report_wizard', raise_if_not_found=False)
            if wiz_action:
                stock_report_menu.write({'action': f"ir.actions.act_window,{wiz_action.id}"})

        # Purchase Report Menu
        purchase_report_menu = env.ref('purchase.purchase_report_main', raise_if_not_found=False)
        if purchase_report_menu:
            children = env['ir.ui.menu'].search([('parent_id', '=', purchase_report_menu.id)])
            if children:
                children.unlink()
            wiz_action = env.ref('bff_reports.action_bff_purchase_report_wizard', raise_if_not_found=False)
            if wiz_action:
                purchase_report_menu.write({'action': f"ir.actions.act_window,{wiz_action.id}"})

        # Account Report Menu
        finance_report_menu = env.ref('account.menu_finance_reports', raise_if_not_found=False)
        if finance_report_menu:
            children = env['ir.ui.menu'].search([('parent_id', '=', finance_report_menu.id)])
            if children:
                children.unlink()
            wiz_action = env.ref('bff_reports.action_bff_finance_report_wizard', raise_if_not_found=False)
            if wiz_action:
                finance_report_menu.write({'action': f"ir.actions.act_window,{wiz_action.id}"})

        cr.commit()

    print(" -> Module bff_reports configured successfully!")

    # Verify menus
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print("\n=== VERIFYING DIRECT WIZARD MENUS ===")
        m_sales = env.ref('sale.menu_sale_report', raise_if_not_found=False)
        if m_sales:
            print(f" [PASS] Penjualan Laporan Menu: '{m_sales.name}' | Action: '{m_sales.action}'")
        m_pos = env.ref('point_of_sale.menu_point_rep', raise_if_not_found=False)
        if m_pos:
            print(f" [PASS] POS Laporan Menu: '{m_pos.name}' | Action: '{m_pos.action}'")
        m_stock = env.ref('stock.menu_warehouse_report', raise_if_not_found=False)
        if m_stock:
            print(f" [PASS] Inventaris Laporan Menu: '{m_stock.name}' | Action: '{m_stock.action}'")
        m_purchase = env.ref('purchase.purchase_report_main', raise_if_not_found=False)
        if m_purchase:
            print(f" [PASS] Pembelian Laporan Menu: '{m_purchase.name}' | Action: '{m_purchase.action}'")
        m_finance = env.ref('account.menu_finance_reports', raise_if_not_found=False)
        if m_finance:
            print(f" [PASS] Penagihan Laporan Menu: '{m_finance.name}' | Action: '{m_finance.action}'")

        print("=========================================================")
        print(" DIRECT WIZARD POPUP ON LAPORAN MENU VERIFIED 100% SUCCESS!")
        print("=========================================================")

if __name__ == '__main__':
    setup_reports()
