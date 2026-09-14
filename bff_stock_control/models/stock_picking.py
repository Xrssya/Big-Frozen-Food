# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        for picking in self:
            # Check outgoing deliveries from internal locations
            if picking.picking_type_code in ('outgoing', 'internal') and picking.location_id.usage == 'internal':
                for move in picking.move_ids:
                    product = move.product_id
                    if product.type == 'consu' and not product.allow_negative_stock:
                        # Storable product
                        demand_qty = move.quantity or move.product_uom_qty
                        min_reserve = product.min_stock_reserve_qty or 0.0
                        sellable_qty = product.qty_available - min_reserve

                        if demand_qty > 0 and (sellable_qty <= 0 or demand_qty > sellable_qty):
                            raise UserError(_(
                                "PERINGATAN STOK DIHENTIKAN!\n\n"
                                "Pengiriman produk '%s' tidak dapat divalidasi karena mencapai batas stok tahan.\n"
                                "• Stok fisik saat ini: %s unit\n"
                                "• Batas minimum tahan: %s unit\n"
                                "• Maksimal dapat dikirim: %s unit\n"
                                "• Jumlah permintaan: %s unit\n\n"
                                "Sistem memblokir pengiriman karena sisa stok tidak boleh kurang dari %s unit."
                            ) % (
                                product.display_name,
                                int(product.qty_available),
                                int(min_reserve),
                                int(max(0, sellable_qty)),
                                int(demand_qty),
                                int(min_reserve)
                            ))

        return super().button_validate()


class StockMove(models.Model):
    _inherit = 'stock.move'

    qty_box = fields.Float(
        string='Jml Box/Kardus',
        digits='Product Unit of Measure',
        default=0.0,
        compute='_compute_qty_box',
        inverse='_inverse_qty_box',
        store=True,
        readonly=False,
        help='Jumlah kardus/box.'
    )
    pcs_per_box = fields.Integer(
        related='product_id.pcs_per_box',
        string='Isi per Box',
        readonly=True
    )

    @api.depends('product_uom_qty', 'quantity', 'product_id', 'product_id.pcs_per_box')
    def _compute_qty_box(self):
        for move in self:
            ratio = move.pcs_per_box or (move.product_id.pcs_per_box if move.product_id else 12) or 1
            qty = move.quantity if (move.picking_id and move.picking_id.state not in ('draft', 'cancel') and move.quantity) else move.product_uom_qty
            if ratio > 0 and qty:
                move.qty_box = round(qty / ratio, 2)
            else:
                move.qty_box = 0.0

    def _inverse_qty_box(self):
        for move in self:
            ratio = move.pcs_per_box or (move.product_id.pcs_per_box if move.product_id else 12) or 1
            if ratio > 0 and move.qty_box:
                target_qty = move.qty_box * ratio
                move.product_uom_qty = target_qty
                move.quantity = target_qty

    @api.onchange('qty_box')
    def _onchange_qty_box(self):
        """When user inputs Box quantity, calculate total Pack/Satuan quantity."""
        for move in self:
            ratio = move.pcs_per_box or (move.product_id.pcs_per_box if move.product_id else 12) or 1
            if move.qty_box and ratio > 0:
                target_qty = move.qty_box * ratio
                move.product_uom_qty = target_qty
                move.quantity = target_qty

    @api.onchange('product_uom_qty', 'quantity', 'product_uom')
    def _onchange_product_qty_sync_box(self):
        """When user inputs Pack quantity, update Box quantity."""
        for move in self:
            ratio = move.pcs_per_box or (move.product_id.pcs_per_box if move.product_id else 12) or 1
            qty = move.quantity if (move.picking_id and move.picking_id.state not in ('draft', 'cancel') and move.quantity) else move.product_uom_qty
            if ratio > 0 and qty:
                move.qty_box = round(qty / ratio, 2)

    @api.onchange('product_id')
    def _onchange_product_id_sync_box(self):
        """Initialize Box quantity when selecting a product."""
        for move in self:
            if move.product_id:
                ratio = move.product_id.pcs_per_box or 12
                qty = move.quantity or move.product_uom_qty
                if qty:
                    move.qty_box = round(qty / ratio, 2) if ratio > 0 else 0.0
                elif ratio > 0:
                    move.qty_box = 1.0
                    move.product_uom_qty = float(ratio)
                    move.quantity = float(ratio)


