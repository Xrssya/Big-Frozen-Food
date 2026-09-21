# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    is_cicilan = fields.Boolean(
        string="Metode Pembayaran Cicilan",
        default=False,
        help="Tandai jika metode pembayaran ini adalah sistem cicilan/penagihan bertahap."
    )

    def _is_write_forbidden(self, fields):
        whitelisted_fields = {'sequence', 'is_cicilan'}
        return bool(fields - whitelisted_fields and self.open_session_ids)

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields_list = super()._load_pos_data_fields(config_id)
        if 'is_cicilan' not in fields_list:
            fields_list.append('is_cicilan')
        return fields_list
