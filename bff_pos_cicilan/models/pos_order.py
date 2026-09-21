# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    is_installment = fields.Boolean(
        string="Transaksi Cicilan",
        compute="_compute_is_installment",
        store=True,
        help="Tandai jika transaksi POS ini menggunakan metode pembayaran cicilan."
    )
    due_date = fields.Date(
        string="Tanggal Jatuh Tempo Cicilan",
        help="Tanggal batas akhir pelunasan cicilan yang ditentukan saat transaksi di kasir POS."
    )

    @api.depends('payment_ids.payment_method_id.is_cicilan', 'payment_ids.payment_method_id.name')
    def _compute_is_installment(self):
        for order in self:
            order.is_installment = any(
                p.payment_method_id.is_cicilan or 'cicilan' in (p.payment_method_id.name or '').lower()
                for p in order.payment_ids
            )

    def _prepare_invoice_vals(self):
        vals = super()._prepare_invoice_vals()
        if self.is_installment:
            vals['is_installment'] = True
            vals['installment_pos_order_id'] = self.id
            if self.due_date:
                vals['invoice_date_due'] = self.due_date
        return vals
