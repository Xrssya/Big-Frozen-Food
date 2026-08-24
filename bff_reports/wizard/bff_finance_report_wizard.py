# -*- coding: utf-8 -*-
import base64
import io
from datetime import datetime
import xlsxwriter

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BffFinanceReportWizard(models.TransientModel):
    _name = 'bff.finance.report.wizard'
    _description = 'Wizard Ekspor Laporan Keuangan Big Frozen Food'

    report_type = fields.Selection([
        ('receivables', 'Laporan Piutang Pelanggan & Agen'),
        ('payables', 'Laporan Tagihan Hutang Pemasok / Supplier'),
        ('pos_sessions', 'Laporan Rekonsiliasi Kas Sesi POS Kasir'),
    ], string='Jenis Laporan Keuangan', default='receivables', required=True)

    def action_export_excel(self):
        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Laporan Keuangan')

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

        is_rec = self.report_type == 'receivables'
        r_title = 'LAPORAN PIUTANG PELANGGAN & AGEN' if is_rec else 'LAPORAN TAGIHAN HUTANG PEMASOK'

        worksheet.write('A1', 'BIG FROZEN FOOD', fmt_company_title)
        worksheet.merge_range('D1:G1', r_title, fmt_report_title)
        worksheet.write('A2', 'Distributor & Retailer Product Food Solution', fmt_meta_left)
        now_str = datetime.now().strftime('%d/%m/%Y %H:%M')
        user_name = self.env.user.name or 'Administrator'
        worksheet.merge_range('D2:G2', f'Dicetak: {now_str} | Oleh: {user_name}', fmt_meta_right)
        worksheet.merge_range('A3:G3', f'Status Faktur: Belum Lunas / Partial', fmt_meta_left)

        m_type = 'out_invoice' if is_rec else 'in_invoice'
        moves = self.env['account.move'].search([
            ('move_type', '=', m_type),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial'])
        ], order='invoice_date_due asc')

        tot_amount = sum(m.amount_total for m in moves)
        tot_residual = sum(m.amount_residual for m in moves)

        card_title1 = 'TOTAL FAKTUR PIUTANG' if is_rec else 'TOTAL FAKTUR HUTANG'
        card_title2 = 'TOTAL SISA PIUTANG' if is_rec else 'TOTAL SISA HUTANG'

        worksheet.merge_range('A5:C5', card_title1, fmt_kpi_label)
        worksheet.merge_range('A6:C6', f'{len(moves)} Faktur', fmt_kpi_val_num)
        worksheet.merge_range('D5:G5', card_title2, fmt_kpi_label)
        worksheet.merge_range('D6:G6', tot_residual, fmt_kpi_val_blue)

        headers = ['No', 'No. Faktur / Tagihan', 'Tanggal Faktur', 'Jatuh Tempo', 'Nama Partner', 'Total Nominal (Rp)', 'Sisa Tagihan (Rp)']
        col_widths = [6, 22, 16, 16, 32, 22, 22]

        for c_idx, h_text in enumerate(headers):
            worksheet.write(7, c_idx, h_text, fmt_table_header)

        row_idx = 8
        idx = 1
        for m in moves:
            fmt = fmt_even if idx % 2 != 0 else fmt_odd
            worksheet.set_row(row_idx, 20)
            worksheet.write(row_idx, 0, idx, fmt['center'])
            worksheet.write(row_idx, 1, m.name, fmt['text'])
            worksheet.write(row_idx, 2, m.invoice_date.strftime('%d/%m/%Y') if m.invoice_date else '', fmt['center'])
            worksheet.write(row_idx, 3, m.invoice_date_due.strftime('%d/%m/%Y') if m.invoice_date_due else '', fmt['center'])
            worksheet.write(row_idx, 4, m.partner_id.name or '', fmt['text'])
            worksheet.write(row_idx, 5, m.amount_total, fmt['amount'])
            worksheet.write(row_idx, 6, m.amount_residual, fmt['amount'])
            row_idx += 1
            idx += 1

        worksheet.set_row(row_idx, 22)
        label_total = 'TOTAL KESELURUHAN PIUTANG' if is_rec else 'TOTAL KESELURUHAN HUTANG'
        worksheet.merge_range(row_idx, 0, row_idx, 4, label_total, fmt_total_label)
        worksheet.write(row_idx, 5, tot_amount, fmt_total_amount)
        worksheet.write(row_idx, 6, tot_residual, fmt_total_amount)

        for c_idx, col_w in enumerate(col_widths):
            worksheet.set_column(c_idx, c_idx, col_w)

        worksheet.freeze_panes(8, 0)

        workbook.close()
        output.seek(0)

        filename = f"Laporan_Keuangan_BFF_{datetime.now().strftime('%d%m%Y')}.xlsx"
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
