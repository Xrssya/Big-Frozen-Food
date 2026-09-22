# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BffInstallmentPaymentWizard(models.TransientModel):
    _name = 'bff.installment.payment.wizard'
    _description = 'Wizard Pembayaran Angsuran Cicilan POS'

    move_id = fields.Many2one(
        'account.move',
        string="Faktur Penagihan",
        required=True,
        readonly=True,
        ondelete='cascade'
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='move_id.partner_id',
        string="Pelanggan",
        readonly=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='move_id.currency_id',
        string="Mata Uang",
        readonly=True
    )
    amount_total = fields.Monetary(
        related='move_id.amount_total',
        string="Total Tagihan Faktur",
        readonly=True,
        currency_field='currency_id'
    )
    amount_paid = fields.Monetary(
        related='move_id.amount_paid',
        string="Sudah Dibayar",
        readonly=True,
        currency_field='currency_id'
    )
    amount_residual = fields.Monetary(
        related='move_id.amount_residual',
        string="Sisa Cicilan Saat Ini",
        readonly=True,
        currency_field='currency_id'
    )
    invoice_date_due = fields.Date(
        related='move_id.invoice_date_due',
        string="Tanggal Jatuh Tempo",
        readonly=True
    )

    payment_type_choice = fields.Selection(
        selection=[
            ('percent', 'Hitung Persentase (%)'),
            ('custom', 'Nominal Custom (Rp)'),
            ('full', 'Pelunasan Penuh (100%)'),
        ],
        string="Mode Opsi Angsuran",
        default='percent',
        required=True
    )
    percent_preset = fields.Selection(
        selection=[
            ('5', '5% dari Total Tagihan'),
            ('10', '10% dari Total Tagihan'),
            ('25', '25% dari Total Tagihan'),
            ('50', '50% dari Total Tagihan'),
        ],
        string="Preset Persentase",
        default='5'
    )
    payment_amount = fields.Monetary(
        string="Nominal Angsuran Dibayar",
        required=True,
        currency_field='currency_id'
    )
    new_residual_amount = fields.Monetary(
        string="Estimasi Sisa Cicilan Setelah Bayar",
        compute="_compute_new_residual_amount",
        currency_field='currency_id'
    )
    journal_id = fields.Many2one(
        'account.journal',
        string="Metode Pembayaran",
        domain="[('type', 'in', ('bank', 'cash'))]",
        required=True
    )
    payment_date = fields.Date(
        string="Tanggal Bayar Angsuran",
        default=fields.Date.context_today,
        required=True
    )
    memo = fields.Char(
        string="Catatan Angsuran",
        help="Memo atau keterangan pembayaran angsuran ini."
    )

    @api.model
    def default_get(self, fields_list):
        res = super(BffInstallmentPaymentWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        if active_model == 'account.move' and active_id:
            move = self.env['account.move'].browse(active_id)
            res['move_id'] = move.id
            # Default payment amount based on 5% or residual
            calc_val = round(move.amount_total * 0.05, 0)
            if calc_val > move.amount_residual or calc_val <= 0:
                calc_val = move.amount_residual
            res['payment_amount'] = calc_val
            res['memo'] = f"Angsuran Cicilan POS - {move.name}"

            # Default payment journal (Cash/Bank)
            default_journal = self.env['account.journal'].search([
                ('type', 'in', ('cash', 'bank')),
                ('company_id', '=', move.company_id.id)
            ], limit=1)
            if default_journal:
                res['journal_id'] = default_journal.id
        return res

    @api.onchange('payment_type_choice', 'percent_preset', 'move_id')
    def _onchange_payment_choice(self):
        if not self.move_id:
            return
        if self.payment_type_choice == 'full':
            self.payment_amount = self.amount_residual
        elif self.payment_type_choice == 'percent' and self.percent_preset:
            pct = float(self.percent_preset) / 100.0
            calc_val = round(self.amount_total * pct, 0)
            if calc_val > self.amount_residual:
                calc_val = self.amount_residual
            self.payment_amount = calc_val

    @api.depends('amount_residual', 'payment_amount')
    def _compute_new_residual_amount(self):
        for wizard in self:
            res = (wizard.amount_residual or 0.0) - (wizard.payment_amount or 0.0)
            wizard.new_residual_amount = max(0.0, res)

    def action_confirm_installment_payment(self):
        self.ensure_one()
        if not self.move_id:
            raise UserError(_("Faktur penagihan tidak ditemukan!"))
        if self.payment_amount <= 0:
            raise UserError(_("Nominal angsuran harus lebih besar dari Rp 0."))
        if self.payment_amount > (self.amount_residual + 0.01):
            raise UserError(_("Nominal angsuran (Rp %s) tidak boleh melebihi sisa cicilan (Rp %s).") % (
                f"{self.payment_amount:,.0f}", f"{self.amount_residual:,.0f}"
            ))

        # Context to create payment via account.payment.register
        ctx = {
            'active_model': 'account.move',
            'active_ids': [self.move_id.id],
        }
        pay_register = self.env['account.payment.register'].with_context(ctx).create({
            'amount': self.payment_amount,
            'payment_date': self.payment_date,
            'journal_id': self.journal_id.id,
            'communication': self.memo or f"Angsuran Cicilan POS - {self.move_id.name}",
        })
        
        # Execute payment registration & reconciliation
        pay_register.action_create_payments()

        # Re-compute move status
        self.move_id._compute_installment_status()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Setoran Angsuran Berhasil!"),
                'message': _("Pembayaran angsuran sebesar Rp %s telah berhasil dicatat untuk faktur %s.") % (
                    f"{self.payment_amount:,.0f}", self.move_id.name
                ),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
