# -*- coding: utf-8 -*-
import base64
import io
from datetime import datetime
import xlsxwriter

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BffSalesReportWizard(models.TransientModel):
    _name = 'bff.sales.report.wizard'
    _description = 'Wizard Ekspor Laporan Penjualan Big Frozen Food'

    date_from = fields.Date(
        string='Tanggal Mulai',
        required=True,
        default=lambda self: fields.Date.context_today(self).replace(day=1)
    )
    date_to = fields.Date(
        string='Tanggal Selesai',
        required=True,
        default=fields.Date.context_today
    )
    report_type = fields.Selection([
        ('turnover', 'Laporan Omset & Tren Penjualan'),
        ('top_products', 'Laporan Top Produk Terlaris'),
        ('pos', 'Laporan Penjualan POS Kasir Toko'),
        ('pos_session', 'Laporan Rekonsiliasi Sesi Kasir POS (Per Sesi)'),
        ('commission', 'Laporan Rekapitulasi & Komisi Kasir'),
    ], string='Jenis Laporan', default='turnover', required=True)

    sales_channel = fields.Selection([
        ('all', 'Semua Kanal (Grosir B2B & POS Retail)'),
        ('b2b', 'Grosir & Agen B2B (Sales Order)'),
        ('pos', 'Retail POS Toko (Point of Sale)'),
    ], string='Kanal Penjualan', default='all', required=True)

    def action_export_excel(self):
        """Generasi dan unduh file Excel (.xlsx) Standar Industri Enterprise (Separated Columns)"""
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_("Tanggal Mulai tidak boleh lebih besar dari Tanggal Selesai!"))

        start_datetime = datetime.combine(self.date_from, datetime.min.time())
        end_datetime = datetime.combine(self.date_to, datetime.max.time())

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Laporan Penjualan')

        worksheet.hide_gridlines(0)
        worksheet.set_paper(9)  # A4
        worksheet.set_landscape()

        # --- COLOR PALETTE (Enterprise Dark Navy & Slate) ---
        NAVY_DARK = '#0F172A'
        NAVY_HEADER = '#1E293B'
        SLATE_LIGHT = '#F8FAFC'
        SLATE_BORDER = '#CBD5E1'
        TEXT_MUTED = '#64748B'

        # --- FORMAT DEFINITIONS ---
        fmt_banner_bg = workbook.add_format({'bg_color': NAVY_DARK})
        fmt_company_title = workbook.add_format({
            'font_name': 'Arial', 'font_size': 16, 'bold': True,
            'font_color': '#FFFFFF', 'valign': 'vcenter', 'bg_color': NAVY_DARK
        })
        fmt_report_title = workbook.add_format({
            'font_name': 'Arial', 'font_size': 13, 'bold': True,
            'font_color': '#38BDF8', 'align': 'right', 'valign': 'vcenter', 'bg_color': NAVY_DARK
        })
        fmt_meta_left = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'font_color': '#94A3B8',
            'valign': 'vcenter', 'bg_color': NAVY_DARK
        })
        fmt_meta_right = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9, 'font_color': '#94A3B8',
            'align': 'right', 'valign': 'vcenter', 'bg_color': NAVY_DARK
        })

        # KPI Card Formats
        fmt_kpi_label = workbook.add_format({
            'font_name': 'Arial', 'font_size': 8, 'bold': True,
            'font_color': TEXT_MUTED, 'align': 'center', 'valign': 'vcenter',
            'bg_color': SLATE_LIGHT, 'top': 1, 'left': 1, 'right': 1, 'border_color': SLATE_BORDER
        })
        fmt_kpi_val_blue = workbook.add_format({
            'font_name': 'Arial', 'font_size': 12, 'bold': True,
            'font_color': '#1E3A8A', 'align': 'center', 'valign': 'vcenter',
            'bg_color': SLATE_LIGHT, 'bottom': 1, 'left': 1, 'right': 1, 'border_color': SLATE_BORDER,
            'num_format': '"Rp "#,##0'
        })
        fmt_kpi_val_num = workbook.add_format({
            'font_name': 'Arial', 'font_size': 12, 'bold': True,
            'font_color': NAVY_DARK, 'align': 'center', 'valign': 'vcenter',
            'bg_color': SLATE_LIGHT, 'bottom': 1, 'left': 1, 'right': 1, 'border_color': SLATE_BORDER
        })
        fmt_kpi_val_green = workbook.add_format({
            'font_name': 'Arial', 'font_size': 12, 'bold': True,
            'font_color': '#059669', 'align': 'center', 'valign': 'vcenter',
            'bg_color': SLATE_LIGHT, 'bottom': 1, 'left': 1, 'right': 1, 'border_color': SLATE_BORDER,
            'num_format': '"Rp "#,##0'
        })
        fmt_kpi_val_cyan = workbook.add_format({
            'font_name': 'Arial', 'font_size': 12, 'bold': True,
            'font_color': '#0891B2', 'align': 'center', 'valign': 'vcenter',
            'bg_color': SLATE_LIGHT, 'bottom': 1, 'left': 1, 'right': 1, 'border_color': SLATE_BORDER,
            'num_format': '"Rp "#,##0'
        })

        # Table Header Format
        fmt_table_header = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9.5, 'bold': True,
            'font_color': '#FFFFFF', 'bg_color': NAVY_HEADER,
            'align': 'center', 'valign': 'vcenter',
            'top': 1, 'bottom': 1, 'left': 1, 'right': 1, 'border_color': NAVY_DARK
        })

        # Data Rows Formats (Zebra Even/Odd)
        def get_data_formats(bg_color):
            return {
                'text': workbook.add_format({
                    'font_name': 'Arial', 'font_size': 9, 'valign': 'vcenter',
                    'bg_color': bg_color, 'border': 1, 'border_color': '#E2E8F0'
                }),
                'center': workbook.add_format({
                    'font_name': 'Arial', 'font_size': 9, 'align': 'center', 'valign': 'vcenter',
                    'bg_color': bg_color, 'border': 1, 'border_color': '#E2E8F0'
                }),
                'amount': workbook.add_format({
                    'font_name': 'Arial', 'font_size': 9, 'align': 'right', 'valign': 'vcenter',
                    'num_format': '"Rp "#,##0', 'bg_color': bg_color, 'border': 1, 'border_color': '#E2E8F0'
                }),
                'qty': workbook.add_format({
                    'font_name': 'Arial', 'font_size': 9, 'align': 'right', 'valign': 'vcenter',
                    'num_format': '#,##0.00', 'bg_color': bg_color, 'border': 1, 'border_color': '#E2E8F0'
                }),
            }

        fmt_even = get_data_formats('#FFFFFF')
        fmt_odd = get_data_formats('#F8FAFC')

        # Total Row Format
        fmt_total_label = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9.5, 'bold': True,
            'font_color': NAVY_DARK, 'align': 'right', 'valign': 'vcenter',
            'bg_color': '#E2E8F0', 'top': 1, 'bottom': 6, 'left': 1, 'right': 1, 'border_color': NAVY_HEADER
        })
        fmt_total_amount = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9.5, 'bold': True,
            'font_color': NAVY_DARK, 'align': 'right', 'valign': 'vcenter',
            'num_format': '"Rp "#,##0', 'bg_color': '#E2E8F0',
            'top': 1, 'bottom': 6, 'left': 1, 'right': 1, 'border_color': NAVY_HEADER
        })
        fmt_total_qty = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9.5, 'bold': True,
            'font_color': NAVY_DARK, 'align': 'right', 'valign': 'vcenter',
            'num_format': '#,##0.00', 'bg_color': '#E2E8F0',
            'top': 1, 'bottom': 6, 'left': 1, 'right': 1, 'border_color': NAVY_HEADER
        })

        title_map = {
            'turnover': 'LAPORAN OMSET & TREN PENJUALAN',
            'top_products': 'LAPORAN TOP PRODUK TERLARIS',
            'pos': 'LAPORAN PENJUALAN POS KASIR TOKO',
            'pos_session': 'LAPORAN REKONSILIASI SESI KASIR POS',
            'commission': 'LAPORAN REKAPITULASI & KOMISI KASIR',
        }
        r_title = title_map.get(self.report_type, 'LAPORAN PENJUALAN')

        # --- 1. BANNER HEADER (Rows 0 to 2) ---
        worksheet.set_row(0, 24)
        worksheet.set_row(1, 18)
        worksheet.set_row(2, 16)
        worksheet.set_row(3, 10)  # spacing
        worksheet.set_row(4, 16)  # KPI label
        worksheet.set_row(5, 24)  # KPI value
        worksheet.set_row(6, 12)  # spacing
        worksheet.set_row(7, 25)  # Table header

        num_cols = 10 if self.report_type == 'turnover' else (11 if self.report_type == 'pos_session' else 6)

        for r in range(3):
            for c in range(num_cols):
                worksheet.write(r, c, '', fmt_banner_bg)

        worksheet.write('A1', 'BIG FROZEN FOOD', fmt_company_title)
        end_col_letter = chr(ord('A') + num_cols - 1)
        start_title_letter = chr(ord('A') + max(0, num_cols - 4))
        worksheet.merge_range(f'{start_title_letter}1:{end_col_letter}1', r_title, fmt_report_title)

        worksheet.write('A2', 'Distributor & Retailer Product Food Solution', fmt_meta_left)
        now_str = datetime.now().strftime('%d/%m/%Y %H:%M')
        user_name = self.env.user.name or 'Administrator'
        worksheet.merge_range(f'{start_title_letter}2:{end_col_letter}2', f'Dicetak: {now_str} | Oleh: {user_name}', fmt_meta_right)

        channel_label = dict(self._fields['sales_channel'].selection).get(self.sales_channel)
        period_str = f"Periode Laporan: {self.date_from.strftime('%d/%m/%Y')} s/d {self.date_to.strftime('%d/%m/%Y')}  |  Kanal: {channel_label}"
        worksheet.merge_range(f'A3:{end_col_letter}3', period_str, fmt_meta_left)

        # --- DATA PROCESSING & TABLE BUILDING ---
        if self.report_type == 'turnover':
            # Separated Customer & Cashier/Salesperson Columns
            headers = [
                'No', 'Tanggal Transaksi', 'No. Dokumen / Struk', 'Kanal Penjualan',
                'Nama Pelanggan', 'Tipe Konsumen', 'Kasir / Salesperson', 'Status Transaksi',
                'Total Subtotal (Rp)', 'Total Omset Penjualan (Rp)'
            ]
            col_widths = [6, 18, 22, 18, 28, 16, 22, 18, 22, 24]

            so_records = []
            if self.sales_channel in ['all', 'b2b']:
                so_records = self.env['sale.order'].search([
                    ('state', 'in', ['sale', 'done']),
                    ('date_order', '>=', start_datetime),
                    ('date_order', '<=', end_datetime)
                ], order='date_order asc')

            pos_records = []
            if self.sales_channel in ['all', 'pos']:
                pos_records = self.env['pos.order'].search([
                    ('state', 'in', ['paid', 'done', 'invoiced']),
                    ('date_order', '>=', start_datetime),
                    ('date_order', '<=', end_datetime)
                ], order='date_order asc')

            total_b2b = sum(so.amount_total for so in so_records)
            total_pos = sum(po.amount_total for po in pos_records)
            grand_omset = total_b2b + total_pos
            total_trx = len(so_records) + len(pos_records)

            # KPI Cards (spanning 10 columns)
            worksheet.merge_range('A5:C5', 'TOTAL OMSET PENJUALAN', fmt_kpi_label)
            worksheet.merge_range('A6:C6', grand_omset, fmt_kpi_val_blue)
            worksheet.merge_range('D5:E5', 'TOTAL TRANSAKSI', fmt_kpi_label)
            worksheet.merge_range('D6:E6', f'{total_trx} Transaksi', fmt_kpi_val_num)
            worksheet.merge_range('F5:H5', 'OMSET GROSIR B2B', fmt_kpi_label)
            worksheet.merge_range('F6:H6', total_b2b, fmt_kpi_val_green)
            worksheet.merge_range('I5:J5', 'OMSET RETAIL POS', fmt_kpi_label)
            worksheet.merge_range('I6:J6', total_pos, fmt_kpi_val_cyan)

            # Table Headers
            for c_idx, h_text in enumerate(headers):
                worksheet.write(7, c_idx, h_text, fmt_table_header)

            row_idx = 8
            idx = 1
            tot_sub = 0.0
            tot_oms = 0.0

            # B2B Records
            for so in so_records:
                fmt = fmt_even if idx % 2 != 0 else fmt_odd
                p_name = so.partner_id.name or 'Pelanggan Umum'
                # Determine Customer Type Classification
                if 'agen' in p_name.lower():
                    cust_type = 'Agen B2B'
                elif 'reseller' in p_name.lower():
                    cust_type = 'Reseller B2B'
                else:
                    cust_type = 'Grosir B2B'

                salesperson = so.user_id.name or 'Salesman B2B'

                worksheet.set_row(row_idx, 20)
                worksheet.write(row_idx, 0, idx, fmt['center'])
                worksheet.write(row_idx, 1, so.date_order.strftime('%d/%m/%Y %H:%M') if so.date_order else '', fmt['center'])
                worksheet.write(row_idx, 2, so.name, fmt['text'])
                worksheet.write(row_idx, 3, 'Grosir B2B', fmt['center'])
                worksheet.write(row_idx, 4, p_name, fmt['text'])
                worksheet.write(row_idx, 5, cust_type, fmt['center'])
                worksheet.write(row_idx, 6, salesperson, fmt['text'])
                worksheet.write(row_idx, 7, 'Dikonfirmasi' if so.state == 'sale' else 'Selesai', fmt['center'])
                worksheet.write(row_idx, 8, so.amount_untaxed, fmt['amount'])
                worksheet.write(row_idx, 9, so.amount_total, fmt['amount'])
                tot_sub += so.amount_untaxed
                tot_oms += so.amount_total
                row_idx += 1
                idx += 1

            # POS Records
            for po in pos_records:
                fmt = fmt_even if idx % 2 != 0 else fmt_odd
                p_name = po.partner_id.name if po.partner_id else 'Pelanggan Walk-in Toko'
                cust_type = 'Retail POS'
                cashier = po.user_id.name or 'Kasir Toko'

                worksheet.set_row(row_idx, 20)
                worksheet.write(row_idx, 0, idx, fmt['center'])
                worksheet.write(row_idx, 1, po.date_order.strftime('%d/%m/%Y %H:%M') if po.date_order else '', fmt['center'])
                worksheet.write(row_idx, 2, po.name, fmt['text'])
                worksheet.write(row_idx, 3, 'Retail POS Toko', fmt['center'])
                worksheet.write(row_idx, 4, p_name, fmt['text'])
                worksheet.write(row_idx, 5, cust_type, fmt['center'])
                worksheet.write(row_idx, 6, cashier, fmt['text'])
                worksheet.write(row_idx, 7, 'Lunas / Terbayar', fmt['center'])
                worksheet.write(row_idx, 8, po.amount_total - po.amount_tax, fmt['amount'])
                worksheet.write(row_idx, 9, po.amount_total, fmt['amount'])
                tot_sub += (po.amount_total - po.amount_tax)
                tot_oms += po.amount_total
                row_idx += 1
                idx += 1

            # Grand Total Row
            worksheet.set_row(row_idx, 22)
            worksheet.merge_range(row_idx, 0, row_idx, 7, 'GRAND TOTAL OMSET PENJUALAN', fmt_total_label)
            worksheet.write(row_idx, 8, tot_sub, fmt_total_amount)
            worksheet.write(row_idx, 9, tot_oms, fmt_total_amount)

        elif self.report_type == 'top_products':
            headers = ['Rank', 'Nama Produk Frozen Food', 'Kategori Produk', 'Total Kuantitas Terjual', 'Satuan', 'Total Omset Produk (Rp)']
            col_widths = [8, 38, 24, 22, 12, 24]

            product_totals = {}
            so_lines = self.env['sale.order.line'].search([
                ('order_id.state', 'in', ['sale', 'done']),
                ('order_id.date_order', '>=', start_datetime),
                ('order_id.date_order', '<=', end_datetime)
            ])
            for line in so_lines:
                pid = line.product_id.id
                if pid not in product_totals:
                    product_totals[pid] = {
                        'name': line.product_id.display_name,
                        'category': line.product_id.categ_id.name or '-',
                        'qty': 0.0,
                        'revenue': 0.0,
                        'uom': line.product_uom.name or 'pcs'
                    }
                product_totals[pid]['qty'] += line.product_uom_qty
                product_totals[pid]['revenue'] += line.price_subtotal

            pos_lines = self.env['pos.order.line'].search([
                ('order_id.state', 'in', ['paid', 'done', 'invoiced']),
                ('order_id.date_order', '>=', start_datetime),
                ('order_id.date_order', '<=', end_datetime)
            ])
            for line in pos_lines:
                pid = line.product_id.id
                if pid not in product_totals:
                    product_totals[pid] = {
                        'name': line.product_id.display_name,
                        'category': line.product_id.categ_id.name or '-',
                        'qty': 0.0,
                        'revenue': 0.0,
                        'uom': line.product_uom_id.name or 'pcs'
                    }
                product_totals[pid]['qty'] += line.qty
                product_totals[pid]['revenue'] += line.price_subtotal_incl

            sorted_prods = sorted(product_totals.values(), key=lambda x: x['revenue'], reverse=True)
            grand_qty = sum(p['qty'] for p in sorted_prods)
            grand_rev = sum(p['revenue'] for p in sorted_prods)

            worksheet.merge_range('A5:B5', 'TOTAL VARIATIF PRODUK', fmt_kpi_label)
            worksheet.merge_range('A6:B6', f'{len(sorted_prods)} Produk', fmt_kpi_val_num)
            worksheet.merge_range('C5:D5', 'TOTAL VOLUME TERJUAL', fmt_kpi_label)
            worksheet.merge_range('C6:D6', f'{grand_qty:,.2f} Unit/Kg', fmt_kpi_val_blue)
            worksheet.merge_range('E5:F5', 'TOTAL OMSET PENJUALAN', fmt_kpi_label)
            worksheet.merge_range('E6:F6', grand_rev, fmt_kpi_val_green)

            for c_idx, h_text in enumerate(headers):
                worksheet.write(7, c_idx, h_text, fmt_table_header)

            row_idx = 8
            rank = 1
            for p in sorted_prods:
                fmt = fmt_even if rank % 2 != 0 else fmt_odd
                worksheet.set_row(row_idx, 20)
                worksheet.write(row_idx, 0, rank, fmt['center'])
                worksheet.write(row_idx, 1, p['name'], fmt['text'])
                worksheet.write(row_idx, 2, p['category'], fmt['text'])
                worksheet.write(row_idx, 3, p['qty'], fmt['qty'])
                worksheet.write(row_idx, 4, p['uom'], fmt['center'])
                worksheet.write(row_idx, 5, p['revenue'], fmt['amount'])
                row_idx += 1
                rank += 1

            worksheet.set_row(row_idx, 22)
            worksheet.merge_range(row_idx, 0, row_idx, 2, 'TOTAL KESELURUHAN PRODUK TERLARIS', fmt_total_label)
            worksheet.write(row_idx, 3, grand_qty, fmt_total_qty)
            worksheet.write(row_idx, 4, '', fmt_total_label)
            worksheet.write(row_idx, 5, grand_rev, fmt_total_amount)

        elif self.report_type == 'pos_session':
            headers = ['No', 'Kode Sesi POS', 'Mesin Kasir', 'Kasir Penanggung Jawab', 'Waktu Buka Sesi', 'Waktu Tutup Sesi', 'Status Sesi', 'Kas Awal (Rp)', 'Total Penjualan (Rp)', 'Kas Akhir Fisik (Rp)', 'Selisih Laci (Rp)']
            col_widths = [6, 18, 22, 26, 18, 18, 16, 20, 22, 20, 20]

            sessions = self.env['pos.session'].search([
                ('start_at', '>=', start_datetime),
                ('start_at', '<=', end_datetime)
            ], order='start_at desc')

            state_map = {
                'opening_control': 'Kontrol Buka',
                'opened': 'Sesi Aktif',
                'closing_control': 'Proses Tutup',
                'closed': 'Tutup Sesi'
            }

            tot_sales = sum(s.total_payments_amount for s in sessions)
            tot_diff = sum(s.cash_register_difference for s in sessions)

            worksheet.merge_range('A5:C5', 'TOTAL SESI KASIR', fmt_kpi_label)
            worksheet.merge_range('A6:C6', f'{len(sessions)} Sesi POS', fmt_kpi_val_num)
            worksheet.merge_range('D5:F5', 'TOTAL PENJUALAN SESI', fmt_kpi_label)
            worksheet.merge_range('D6:F6', tot_sales, fmt_kpi_val_blue)
            worksheet.merge_range('G5:I5', 'TOTAL SELISIH KAS LACI', fmt_kpi_label)
            worksheet.merge_range('G6:I6', tot_diff, fmt_kpi_val_cyan)

            for c_idx, h_text in enumerate(headers):
                worksheet.write(7, c_idx, h_text, fmt_table_header)

            row_idx = 8
            idx = 1
            for s in sessions:
                fmt = fmt_even if idx % 2 != 0 else fmt_odd
                worksheet.set_row(row_idx, 20)
                worksheet.write(row_idx, 0, idx, fmt['center'])
                worksheet.write(row_idx, 1, s.name, fmt['text'])
                worksheet.write(row_idx, 2, s.config_id.name or '', fmt['text'])
                worksheet.write(row_idx, 3, s.user_id.name or '', fmt['text'])
                worksheet.write(row_idx, 4, s.start_at.strftime('%d/%m/%Y %H:%M') if s.start_at else '', fmt['center'])
                worksheet.write(row_idx, 5, s.stop_at.strftime('%d/%m/%Y %H:%M') if s.stop_at else '-', fmt['center'])
                worksheet.write(row_idx, 6, state_map.get(s.state, s.state), fmt['center'])
                worksheet.write(row_idx, 7, s.cash_register_balance_start, fmt['amount'])
                worksheet.write(row_idx, 8, s.total_payments_amount, fmt['amount'])
                worksheet.write(row_idx, 9, s.cash_register_balance_end_real, fmt['amount'])
                worksheet.write(row_idx, 10, s.cash_register_difference, fmt['amount'])
                row_idx += 1
                idx += 1

            worksheet.set_row(row_idx, 22)
            worksheet.merge_range(row_idx, 0, row_idx, 7, 'TOTAL REKONSILIASI KAS SESI POS', fmt_total_label)
            worksheet.write(row_idx, 8, tot_sales, fmt_total_amount)
            worksheet.write(row_idx, 9, '', fmt_total_label)
            worksheet.write(row_idx, 10, tot_diff, fmt_total_amount)

        else:
            headers = ['No', 'Tanggal Transaksi', 'No. Dokumen / Struk', 'Nama Kasir', 'Status Transaksi', 'Total Omset (Rp)']
            col_widths = [6, 18, 24, 28, 18, 24]

            pos_records = self.env['pos.order'].search([
                ('state', 'in', ['paid', 'done', 'invoiced']),
                ('date_order', '>=', start_datetime),
                ('date_order', '<=', end_datetime)
            ], order='date_order asc')

            tot_oms = sum(po.amount_total for po in pos_records)
            worksheet.merge_range('A5:C5', 'TOTAL PENJUALAN POS RETAIL', fmt_kpi_label)
            worksheet.merge_range('A6:C6', tot_oms, fmt_kpi_val_blue)

            for c_idx, h_text in enumerate(headers):
                worksheet.write(7, c_idx, h_text, fmt_table_header)

            row_idx = 8
            idx = 1
            for po in pos_records:
                fmt = fmt_even if idx % 2 != 0 else fmt_odd
                worksheet.set_row(row_idx, 20)
                worksheet.write(row_idx, 0, idx, fmt['center'])
                worksheet.write(row_idx, 1, po.date_order.strftime('%d/%m/%Y %H:%M') if po.date_order else '', fmt['center'])
                worksheet.write(row_idx, 2, po.name, fmt['text'])
                worksheet.write(row_idx, 3, po.user_id.name or '', fmt['text'])
                worksheet.write(row_idx, 4, 'Lunas / Terbayar', fmt['center'])
                worksheet.write(row_idx, 5, po.amount_total, fmt['amount'])
                row_idx += 1
                idx += 1

            worksheet.set_row(row_idx, 22)
            worksheet.merge_range(row_idx, 0, row_idx, 4, 'TOTAL OMSET POS RETAIL TOKO', fmt_total_label)
            worksheet.write(row_idx, 5, tot_oms, fmt_total_amount)

        # Set Column Widths & Freeze Panes
        for c_idx, col_w in enumerate(col_widths):
            worksheet.set_column(c_idx, c_idx, col_w)

        worksheet.freeze_panes(8, 0)

        workbook.close()
        output.seek(0)

        filename = f"Laporan_Penjualan_BFF_{self.date_from.strftime('%d%m%Y')}_{self.date_to.strftime('%d%m%Y')}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
