# -*- coding: utf-8 -*-
from odoo import models

class PosConfig(models.Model):
    _inherit = 'pos.config'

    def _action_to_open_ui(self):
        res = super(PosConfig, self)._action_to_open_ui()
        if isinstance(res, dict) and 'url' in res:
            url = res['url']
            if '&debug=' in url:
                url = url.split('&debug=')[0]
            elif '?debug=' in url:
                url = url.split('?debug=')[0]
            res['url'] = url
        return res
