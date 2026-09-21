# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_installment = fields.Boolean(
        string="Transaksi Cicilan POS",
        default=False,
        index=True,
        help="Menandai bahwa faktur ini berasal dari pembayaran cicilan POS."
    )
    installment_pos_order_id = fields.Many2one(
        'pos.order',
        string="Order POS Asal",
        readonly=True,
        ondelete='set null',
        help="Order POS asal dari transaksi cicilan ini."
    )
    installment_status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('ongoing', 'Masih Nyicil'),
            ('overdue', 'Sudah Jatuh Tempo'),
            ('paid', 'Lunas'),
        ],
        string="Status Cicilan",
        compute="_compute_installment_status",
        store=True,
        help="Status pembayaran cicilan pelanggan."
    )
    amount_paid = fields.Monetary(
        string="Sudah Dibayar",
        compute="_compute_installment_amounts",
        store=True,
        currency_field='currency_id',
        help="Total nominal yang sudah dibayar (DP + Angsuran)."
    )

    @api.depends('state', 'payment_state', 'is_installment', 'invoice_date_due')
    def _compute_installment_status(self):
        today = fields.Date.today()
        for move in self:
            if not move.is_installment:
                move.installment_status = False
            elif move.state == 'draft':
                move.installment_status = 'draft'
            elif move.payment_state in ('paid', 'reversed', 'in_payment'):
                move.installment_status = 'paid'
            elif move.invoice_date_due and move.invoice_date_due < today:
                move.installment_status = 'overdue'
            else:
                move.installment_status = 'ongoing'

    @api.depends('amount_total', 'amount_residual', 'is_installment')
    def _compute_installment_amounts(self):
        for move in self:
            if move.is_installment:
                move.amount_paid = move.amount_total - move.amount_residual
            else:
                move.amount_paid = 0.0

    def action_register_installment_payment(self):
        """
        Action tombol 'Bayar Cicilan' untuk membuka wizard pembayaran angsuran.
        """
        self.ensure_one()
        return {
            'name': 'Bayar Angsuran / Cicilan',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.ids,
                'default_amount': self.amount_residual,
            }
        }
