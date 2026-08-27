# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, time

class CashierCommissionReport(models.Model):
    _name = 'cashier.commission.report'
    _description = 'Rekapitulasi Komisi & Bonus Penjualan Kasir'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_to desc, id desc'

    name = fields.Char(
        string='Nomor Rekap',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Baru')
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Kasir / Karyawan',
        domain="[('bff_role', '=', 'kasir')]",
        required=True
    )

    user_id = fields.Many2one(
        'res.users',
        string='User Odoo Kasir',
        related='employee_id.user_id',
        store=True,
        readonly=True
    )

    date_from = fields.Date(
        string='Periode Mulai',
        default=fields.Date.context_today,
        required=True
    )

    date_to = fields.Date(
        string='Periode Sampai',
        default=fields.Date.context_today,
        required=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Hitung Komisi'),
        ('approved', 'Disetujui'),
        ('paid', 'Dibayarkan')
    ], string='Status Laporan', default='draft', tracking=True)

    commission_rate_percent = fields.Float(
        string='Rate Komisi Omset (%)',
        related='employee_id.commission_rate_percent',
        readonly=True
    )

    clearance_bonus_percent = fields.Float(
        string='Rate Bonus Clearance (%)',
        related='employee_id.clearance_bonus_percent',
        readonly=True
    )

    total_pos_orders = fields.Integer(
        string='Total Transaksi POS',
        compute='_compute_totals',
        store=True
    )

    total_omset = fields.Monetary(
        string='Total Omset Penjualan (Rp)',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )

    total_clearance_sales = fields.Monetary(
        string='Total Omset Cuci Gudang (Rp)',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )

    general_commission_amount = fields.Monetary(
        string='Jumlah Komisi Omset (Rp)',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )

    clearance_bonus_amount = fields.Monetary(
        string='Jumlah Bonus Cuci Gudang (Rp)',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )

    total_commission_payout = fields.Monetary(
        string='Total Komisi Diterima (Rp)',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Mata Uang',
        default=lambda self: self.env.company.currency_id
    )

    line_ids = fields.One2many(
        'cashier.commission.report.line',
        'report_id',
        string='Detail Transaksi POS',
        copy=False
    )

    notes = fields.Text(string='Catatan / Keterangan')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Baru')) == _('Baru'):
                vals['name'] = self.env['ir.sequence'].next_by_code('cashier.commission.report') or _('COMM-001')
        return super().create(vals_list)

    @api.depends('line_ids', 'line_ids.price_subtotal', 'line_ids.is_near_expiry', 'employee_id.commission_rate_percent', 'employee_id.clearance_bonus_percent')
    def _compute_totals(self):
        for rep in self:
            orders = set(rep.line_ids.mapped('order_id'))
            rep.total_pos_orders = len(orders)

            total_omset = sum(rep.line_ids.mapped('price_subtotal'))
            clearance_lines = rep.line_ids.filtered(lambda l: l.is_near_expiry)
            total_clearance = sum(clearance_lines.mapped('price_subtotal'))

            gen_rate = (rep.employee_id.commission_rate_percent or 1.0) / 100.0
            clear_rate = (rep.employee_id.clearance_bonus_percent or 5.0) / 100.0

            gen_comm = total_omset * gen_rate
            clear_bonus = total_clearance * clear_rate

            rep.total_omset = total_omset
            rep.total_clearance_sales = total_clearance
            rep.general_commission_amount = gen_comm
            rep.clearance_bonus_amount = clear_bonus
            rep.total_commission_payout = gen_comm + clear_bonus

    def action_calculate_commission(self):
        for rep in self:
            if not rep.employee_id:
                raise UserError(_("Harap pilih Kasir / Karyawan terlebih dahulu!"))

            rep.line_ids.unlink()

            dt_from = datetime.combine(rep.date_from, time.min)
            dt_to = datetime.combine(rep.date_to, time.max)

            domain = [
                ('date_order', '>=', dt_from),
                ('date_order', '<=', dt_to),
                ('state', 'in', ['paid', 'done', 'invoiced'])
            ]
            if rep.user_id:
                domain.append(('user_id', '=', rep.user_id.id))
            elif rep.employee_id.user_id:
                domain.append(('user_id', '=', rep.employee_id.user_id.id))

            pos_orders = self.env['pos.order'].search(domain)

            lines_data = []
            for order in pos_orders:
                for line in order.lines:
                    prod = line.product_id
                    is_near_exp = getattr(prod, 'is_near_expiry', False)
                    lines_data.append((0, 0, {
                        'order_id': order.id,
                        'product_id': prod.id,
                        'qty': line.qty,
                        'price_subtotal': line.price_subtotal_incl or (line.qty * line.price_unit),
                        'is_near_expiry': is_near_exp,
                    }))

            if lines_data:
                rep.write({
                    'line_ids': lines_data,
                    'state': 'calculated'
                })
            else:
                rep.write({'state': 'calculated'})
        return True

    def action_approve(self):
        for rep in self:
            rep.write({'state': 'approved'})
        return True

    def action_pay(self):
        for rep in self:
            rep.write({'state': 'paid'})
        return True

    def action_reset_draft(self):
        for rep in self:
            rep.write({'state': 'draft'})
        return True


class CashierCommissionReportLine(models.Model):
    _name = 'cashier.commission.report.line'
    _description = 'Detail Baris Transaksi Komisi Kasir'

    report_id = fields.Many2one(
        'cashier.commission.report',
        string='Laporan Komisi',
        ondelete='cascade',
        required=True
    )

    order_id = fields.Many2one(
        'pos.order',
        string='Transaksi POS',
        required=True
    )

    date_order = fields.Datetime(
        string='Tanggal Transaksi',
        related='order_id.date_order',
        store=True
    )

    product_id = fields.Many2one(
        'product.product',
        string='Produk Frozen Food',
        required=True
    )

    qty = fields.Float(string='Jumlah (Qty)')

    price_subtotal = fields.Monetary(
        string='Subtotal Transaksi (Rp)',
        currency_field='currency_id'
    )

    is_near_expiry = fields.Boolean(
        string='Produk Cuci Gudang?',
        help='True jika produk termasuk dalam kategori Mendekati Expired (Clearance Sale).'
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='report_id.currency_id'
    )
