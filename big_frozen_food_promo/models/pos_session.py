# -*- coding: utf-8 -*-
from odoo import models, api

class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        data_models = super()._load_pos_data_models(config_id)
        if 'product.discount.promo' not in data_models:
            data_models.append('product.discount.promo')
        return data_models

