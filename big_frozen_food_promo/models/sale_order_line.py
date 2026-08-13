# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_id_apply_promo_discount(self):
        if not self.product_id:
            return
        product_tmpl = self.product_id.product_tmpl_id
        now = fields.Datetime.now()
        qty = self.product_uom_qty or 1.0
        
        # Search active promos
        domain = [
            ('active', '=', True),
            '|', ('date_start', '=', False), ('date_start', '<=', now),
            '|', ('date_end', '=', False), ('date_end', '>=', now),
        ]
        promos = self.env['product.discount.promo'].search(domain, order='id desc')
        
        found_disc = 0.0
        for promo in promos:
            disc = promo.get_applicable_discount(
                product_tmpl,
                list_price=self.price_unit or product_tmpl.list_price,
                qty=qty
            )
            if disc > 0:
                found_disc = disc
                break
        self.discount = found_disc

