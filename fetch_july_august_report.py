#!/usr/bin/env python3
import sys
from datetime import datetime

sys.path.insert(0, '/home/setyo/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'big_frozen_food'

def run():
    odoo.tools.config.parse_config(['-c', '/home/setyo/developer/odoo/odoo-BigFrozenFood/big_frozen_food.conf', '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("==========================================================================")
        print("        REKAPITULASI PEMBELIAN & PENJUALAN (1 JULI 2026 - 10 AGUSTUS 2026)")
        print("==========================================================================")

        # 1. Purchase Orders Summary
        pos = env['purchase.order'].search([('date_order', '>=', '2026-07-01'), ('date_order', '<=', '2026-08-10 23:59:59')])
        total_po_amount = sum(pos.mapped('amount_total'))
        total_po_lines = sum(len(po.order_line) for po in pos)
        total_po_qty = sum(sum(po.order_line.mapped('product_qty')) for po in pos)

        print(f"\n📦 [PEMBELIAN / PURCHASE ORDERS] Total PO: {len(pos)} Transaksi")
        print(f"   • Total Nilai Pembelian : Rp {total_po_amount:,.0f}")
        print(f"   • Total Barang Diterima : {total_po_qty:,.0f} Pcs ({total_po_lines} Jenis Baris Order)")
        print("   • Rincian per Supplier/Vendor:")
        
        vendor_breakdown = {}
        for po in pos:
            v_name = po.partner_id.name
            vendor_breakdown[v_name] = vendor_breakdown.get(v_name, 0) + po.amount_total
        for v_name, val in vendor_breakdown.items():
            print(f"     - {v_name:<25}: Rp {val:,.0f}")

        # 2. B2B Sales Orders & Invoices Summary
        sos = env['sale.order'].search([('date_order', '>=', '2026-07-01'), ('date_order', '<=', '2026-08-10 23:59:59')])
        total_so_amount = sum(sos.mapped('amount_total'))
        total_so_qty = sum(sum(so.order_line.mapped('product_uom_qty')) for so in sos)

        invoices = env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', '2026-07-01'),
            ('invoice_date', '<=', '2026-08-10')
        ])
        total_inv_amount = sum(invoices.mapped('amount_total'))

        print(f"\n🚚 [PENJUALAN GROSIR B2B / SALES ORDERS & INVOICES] Total SO: {len(sos)} Transaksi | Invoice: {len(invoices)} Faktur")
        print(f"   • Total Omset B2B (SO)   : Rp {total_so_amount:,.0f}")
        print(f"   • Total Invoiced (Post) : Rp {total_inv_amount:,.0f}")
        print(f"   • Total Barang Terjual  : {total_so_qty:,.0f} Pcs")
        print("   • Rincian Penjualan B2B per Pelanggan:")

        cust_breakdown = {}
        for so in sos:
            c_name = so.partner_id.name
            cust_breakdown[c_name] = cust_breakdown.get(c_name, 0) + so.amount_total
        for c_name, val in sorted(cust_breakdown.items(), key=lambda x: x[1], reverse=True):
            print(f"     - {c_name:<32}: Rp {val:,.0f}")

        # 3. POS Retail & Wholesale Summary
        pos_orders = env['pos.order'].search([('date_order', '>=', '2026-07-01'), ('date_order', '<=', '2026-08-10 23:59:59')])
        total_pos_revenue = sum(pos_orders.mapped('amount_total'))
        total_pos_qty = sum(sum(po.lines.mapped('qty')) for po in pos_orders)

        print(f"\n🛒 [PENJUALAN KASIR POS / POINT OF SALE] Total Order: {len(pos_orders)} Transaksi Kasir")
        print(f"   • Total Omset POS Kasir : Rp {total_pos_revenue:,.0f}")
        print(f"   • Total Barang Terjual  : {total_pos_qty:,.0f} Pcs")
        
        # Payment method breakdown
        pm_breakdown = {}
        for p_order in pos_orders:
            for payment in p_order.payment_ids:
                pm_name = payment.payment_method_id.name
                pm_breakdown[pm_name] = pm_breakdown.get(pm_name, 0) + payment.amount

        print("   • Rincian per Metode Pembayaran POS:")
        for pm_name, val in pm_breakdown.items():
            print(f"     - {pm_name:<25}: Rp {val:,.0f}")

        # 4. Total Financial Overview
        grand_sales_revenue = total_so_amount + total_pos_revenue
        print("\n==========================================================================")
        print(f" 💰 TOTAL KESELURUHAN OMSET PENJUALAN (1 JULI - 10 AGUSTUS 2026): Rp {grand_sales_revenue:,.0f}")
        print(f" 🏭 TOTAL KESELURUHAN BELANJA STOK / PO (1 JULI - 10 AGUSTUS 2026): Rp {total_po_amount:,.0f}")
        print("==========================================================================")

if __name__ == '__main__':
    run()
