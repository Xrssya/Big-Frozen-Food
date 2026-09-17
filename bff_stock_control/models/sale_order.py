# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_box = fields.Float(
        string='Jml Box/Kardus',
        digits='Product Unit of Measure',
        default=0.0,
        help='Jumlah kardus/box yang dijual.'
    )
    pcs_per_box = fields.Integer(
        related='product_id.pcs_per_box',
        string='Isi per Box',
        readonly=True
    )

    @api.onchange('product_packaging_id', 'product_packaging_qty')
    def _onchange_product_packaging_sync_qty(self):
        """When user selects dynamic packaging or changes packaging qty, calculate total product_uom_qty."""
        for line in self:
            if line.product_packaging_id and line.product_packaging_qty:
                ratio = line.product_packaging_id.qty or 1.0
                line.product_uom_qty = line.product_packaging_qty * ratio
                line.qty_box = line.product_packaging_qty

    @api.onchange('qty_box')
    def _onchange_qty_box(self):
        """When user inputs Box quantity, calculate total Pack/Satuan quantity."""
        for line in self:
            if line.product_packaging_id:
                ratio = line.product_packaging_id.qty or 1.0
                line.product_packaging_qty = line.qty_box
                line.product_uom_qty = line.qty_box * ratio
            else:
                ratio = line.pcs_per_box or (line.product_id.pcs_per_box if line.product_id else 12) or 1
                if line.qty_box and ratio > 0:
                    line.product_uom_qty = line.qty_box * ratio

    @api.onchange('product_uom_qty', 'product_uom')
    def _onchange_product_uom_qty_sync_box(self):
        """When user inputs Pack quantity, update Box quantity and packaging qty."""
        for line in self:
            if line.product_packaging_id:
                ratio = line.product_packaging_id.qty or 1.0
                if ratio > 0 and line.product_uom_qty:
                    line.product_packaging_qty = round(line.product_uom_qty / ratio, 2)
                    line.qty_box = line.product_packaging_qty
            else:
                ratio = line.pcs_per_box or (line.product_id.pcs_per_box if line.product_id else 12) or 1
                if ratio > 0 and line.product_uom_qty:
                    line.qty_box = round(line.product_uom_qty / ratio, 2)

    @api.onchange('product_id')
    def _onchange_product_id_sync_box(self):
        """Initialize Packaging / Box quantity when selecting a product."""
        for line in self:
            if line.product_id:
                packagings = line.product_id.packaging_ids.filtered(lambda p: p.sales) or line.product_id.packaging_ids
                if packagings:
                    line.product_packaging_id = packagings[0]
                    line.product_packaging_qty = 1.0
                    line.product_uom_qty = packagings[0].qty or 1.0
                    line.qty_box = 1.0
                else:
                    ratio = line.product_id.pcs_per_box or 12
                    if line.product_uom_qty:
                        line.qty_box = round(line.product_uom_qty / ratio, 2) if ratio > 0 else 0.0
                    else:
                        line.qty_box = 1.0
                        line.product_uom_qty = float(ratio)
