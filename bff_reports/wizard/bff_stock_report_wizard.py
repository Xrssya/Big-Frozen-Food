# -*- coding: utf-8 -*-
import base64
import io
from datetime import datetime
import xlsxwriter

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BffStockReportWizard(models.TransientModel):
    _name = 'bff.stock.report.wizard'
    _description = 'Wizard Ekspor Laporan Stok Gudang Big Frozen Food'

    report_type = fields.Selection([
        ('stock_level', 'Laporan Sebaran & Level Stok Produk'),
        ('low_stock', 'Laporan Peringatan Stok Menipis'),
        ('fefo_expiry', 'Laporan Watchlist Kadaluarsa FEFO'),
        ('movements', 'Laporan Mutasi & Pergerakan Barang Beku'),
    ], string='Jenis Laporan Stok', default='stock_level', required=True)

    categ_id = fields.Many2one('product.category', string='Kategori Produk')

    def action_export_excel(self):
        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Laporan Stok')

        worksheet.hide_gridlines(0)
        worksheet.set_paper(9)  # A4
        worksheet.set_landscape()

        NAVY_DARK = '#0F172A'
        NAVY_HEADER = '#1E293B'
        SLATE_LIGHT = '#F8FAFC'
        SLATE_BORDER = '#CBD5E1'
        TEXT_MUTED = '#64748B'

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
            'num_format': '#,##0'
        })

        fmt_table_header = workbook.add_format({
            'font_name': 'Arial', 'font_size': 9.5, 'bold': True,
            'font_color': '#FFFFFF', 'bg_color': NAVY_HEADER,
            'align': 'center', 'valign': 'vcenter',
            'top': 1, 'bottom': 1, 'left': 1, 'right': 1, 'border_color': NAVY_DARK
        })

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
                    'num_format': '#,##0', 'bg_color': bg_color, 'border': 1, 'border_color': '#E2E8F0'
                }),
            }

        fmt_even = get_data_formats('#FFFFFF')
        fmt_odd = get_data_formats('#F8FAFC')

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
            'num_format': '#,##0', 'bg_color': '#E2E8F0',
            'top': 1, 'bottom': 6, 'left': 1, 'right': 1, 'border_color': NAVY_HEADER
        })

        worksheet.set_row(0, 24)
        worksheet.set_row(1, 18)
        worksheet.set_row(2, 16)
        worksheet.set_row(3, 10)
        worksheet.set_row(4, 16)
        worksheet.set_row(5, 24)
        worksheet.set_row(6, 12)
        worksheet.set_row(7, 25)

        num_cols = 7
        for r in range(3):
            for c in range(num_cols):
                worksheet.write(r, c, '', fmt_banner_bg)

        worksheet.write('A1', 'BIG FROZEN FOOD', fmt_company_title)
        worksheet.merge_range('D1:G1', 'LAPORAN STOK & LOGISTIK COLD STORAGE', fmt_report_title)
        worksheet.write('A2', 'Distributor & Retailer Product Food Solution', fmt_meta_left)
        now_str = datetime.now().strftime('%d/%m/%Y %H:%M')
        user_name = self.env.user.name or 'Administrator'
        worksheet.merge_range('D2:G2', f'Dicetak: {now_str} | Oleh: {user_name}', fmt_meta_right)
        categ_str = self.categ_id.name if self.categ_id else 'Semua Kategori Produk'
        worksheet.merge_range('A3:G3', f'Kategori Produk: {categ_str}', fmt_meta_left)

        if 'is_storable' in self.env['product.product']._fields:
            domain = [('is_storable', '=', True)]
        else:
            domain = [('type', '=', 'consu')]
        if self.categ_id and self.categ_id.name.lower() != 'all' and self.categ_id.id != 1:
            domain.append(('categ_id', 'child_of', self.categ_id.id))
        products = self.env['product.product'].search(domain, order='name asc')

        tot_qty = sum(p.qty_available for p in products)
        tot_val = sum(p.qty_available * (p.standard_price or p.list_price * 0.7) for p in products)

        worksheet.merge_range('A5:B5', 'TOTAL ITEM PRODUK', fmt_kpi_label)
        worksheet.merge_range('A6:B6', f'{len(products)} Produk', fmt_kpi_val_num)
        worksheet.merge_range('C5:D5', 'TOTAL VOLUME STOK FISIK', fmt_kpi_label)
        worksheet.merge_range('C6:D6', tot_qty, fmt_kpi_val_green)
        worksheet.merge_range('E5:G5', 'ESTIMASI VALUASI NILAI STOK', fmt_kpi_label)
        worksheet.merge_range('E6:G6', tot_val, fmt_kpi_val_blue)

        headers = ['No', 'Nama Produk Frozen Food', 'Kategori Produk', 'Harga Modal (Rp)', 'Stok Fisik Tersedia', 'Satuan', 'Estimasi Nilai Stok (Rp)']
        col_widths = [6, 38, 24, 18, 20, 12, 22]

        for c_idx, h_text in enumerate(headers):
            worksheet.write(7, c_idx, h_text, fmt_table_header)

        row_idx = 8
        idx = 1
        for p in products:
            fmt = fmt_even if idx % 2 != 0 else fmt_odd
            val = p.qty_available * (p.standard_price or p.list_price * 0.7)
            worksheet.set_row(row_idx, 20)
            worksheet.write(row_idx, 0, idx, fmt['center'])
            worksheet.write(row_idx, 1, p.display_name, fmt['text'])
            worksheet.write(row_idx, 2, p.categ_id.name or '-', fmt['text'])
            worksheet.write(row_idx, 3, p.standard_price, fmt['amount'])
            worksheet.write(row_idx, 4, p.qty_available, fmt['qty'])
            worksheet.write(row_idx, 5, p.uom_id.name or 'pcs', fmt['center'])
            worksheet.write(row_idx, 6, val, fmt['amount'])
            row_idx += 1
            idx += 1

        worksheet.set_row(row_idx, 22)
        worksheet.merge_range(row_idx, 0, row_idx, 3, 'TOTAL KESELURUHAN STOK COLD STORAGE', fmt_total_label)
        worksheet.write(row_idx, 4, tot_qty, fmt_total_qty)
        worksheet.write(row_idx, 5, '', fmt_total_label)
        worksheet.write(row_idx, 6, tot_val, fmt_total_amount)

        for c_idx, col_w in enumerate(col_widths):
            worksheet.set_column(c_idx, c_idx, col_w)

        worksheet.freeze_panes(8, 0)

        workbook.close()
        output.seek(0)

        filename = f"Laporan_Stok_BFF_{datetime.now().strftime('%d%m%Y')}.xlsx"
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
