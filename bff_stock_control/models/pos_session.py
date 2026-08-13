# -*- coding: utf-8 -*-
from odoo import models

class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        if result and 'search_params' in result and 'fields' in result['search_params']:
            for field in ['qty_available', 'min_stock_alert_qty', 'is_low_stock', 'allow_negative_stock']:
                if field not in result['search_params']['fields']:
                    result['search_params']['fields'].append(field)
        return result
