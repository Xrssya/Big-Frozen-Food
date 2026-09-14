# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    qty_box = fields.Float(
        string='Jml Box/Kardus',
        digits='Product Unit of Measure',
        default=0.0,
        help='Jumlah kardus/box yang dibeli.'
    )
    pcs_per_box = fields.Integer(
        related='product_id.pcs_per_box',
        string='Isi per Box',
        readonly=True
    )

    @api.onchange('qty_box')
    def _onchange_qty_box(self):
        """When user inputs Box quantity, calculate total Pack/Satuan quantity."""
        for line in self:
            ratio = line.pcs_per_box or (line.product_id.pcs_per_box if line.product_id else 12) or 1
            if line.qty_box and ratio > 0:
                line.product_qty = line.qty_box * ratio

    @api.onchange('product_qty', 'product_uom')
    def _onchange_product_qty_sync_box(self):
        """When user inputs Pack quantity, update Box quantity."""
        for line in self:
            ratio = line.pcs_per_box or (line.product_id.pcs_per_box if line.product_id else 12) or 1
            if ratio > 0 and line.product_qty:
                line.qty_box = round(line.product_qty / ratio, 2)

    @api.onchange('product_id')
    def _onchange_product_id_sync_box(self):
        """Initialize Box quantity when selecting a product."""
        for line in self:
            if line.product_id:
                ratio = line.product_id.pcs_per_box or 12
                if line.product_qty:
                    line.qty_box = round(line.product_qty / ratio, 2) if ratio > 0 else 0.0
                else:
                    line.qty_box = 1.0
                    line.product_qty = float(ratio)
