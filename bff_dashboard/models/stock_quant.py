# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    stock_valuation_amount = fields.Monetary(
        string="Nilai Stok (Rp)",
        compute="_compute_stock_valuation_amount",
        currency_field="currency_id",
        store=True,
    )

    @api.depends('quantity', 'product_id', 'product_id.standard_price', 'product_id.list_price')
    def _compute_stock_valuation_amount(self):
        for quant in self:
            price = quant.product_id.standard_price or (quant.product_id.list_price * 0.7)
            quant.stock_valuation_amount = (quant.quantity or 0.0) * price
