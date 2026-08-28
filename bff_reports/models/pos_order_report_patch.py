# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    province_id = fields.Many2one(
        'res.country.state',
        string='Provinsi / Wilayah',
        related='company_id.state_id',
        store=True,
        readonly=True
    )
    printed_receipt_count = fields.Integer(
        string='Jumlah Struk Dicetak',
        default=1,
        store=True,
        readonly=True,
        help='Jumlah lembar/nomor struk thermal yang telah dicetak untuk transaksi cabang ini.'
    )

    @api.model
    def web_search_read(self, domain=None, specification=None, offset=0, limit=None, order=None, count_limit=None):
        ctx = self.env.context
        if not any(k.startswith('search_default_group_by') for k in ctx.keys()):
            self = self.with_context(
                search_default_group_by_province=1,
                search_default_group_by_company=1,
                search_default_group_by_user=1,
            )
        return super(PosOrder, self).web_search_read(
            domain=domain,
            specification=specification,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit,
        )
