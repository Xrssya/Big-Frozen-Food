# -*- coding: utf-8 -*-
from odoo import models, api, _
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

