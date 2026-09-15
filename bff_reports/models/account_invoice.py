# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    qty_dus_pack_str = fields.Char(
        string='Jumlah Dus/Pack',
        compute='_compute_qty_dus_pack_str'
    )

    @api.depends('quantity', 'product_id', 'product_id.pcs_per_dus')
    def _compute_qty_dus_pack_str(self):
        for line in self:
            if line.product_id:
                line.qty_dus_pack_str = line.product_id.format_qty_dus_pack(line.quantity)
            else:
                qty_int = int(round(line.quantity))
                line.qty_dus_pack_str = f"{qty_int} Pack"


class AccountMove(models.Model):
    _inherit = 'account.move'

    total_dus_pack_str = fields.Char(
        string='Total Volume Dus/Pack',
        compute='_compute_total_dus_pack_str'
    )

    @api.depends('invoice_line_ids.quantity', 'invoice_line_ids.product_id', 'invoice_line_ids.product_id.pcs_per_dus')
    def _compute_total_dus_pack_str(self):
        for move in self:
            total_dus = 0
            total_pack = 0
            lines = move.invoice_line_ids.filtered(lambda l: not l.display_type or l.display_type == 'product')
            for line in lines:
                pcs_per_dus = (line.product_id and line.product_id.pcs_per_dus) or 10
                qty_int = int(round(line.quantity))
                if pcs_per_dus > 0:
                    total_dus += qty_int // pcs_per_dus
                    total_pack += qty_int % pcs_per_dus
                else:
                    total_pack += qty_int
            
            if total_dus > 0 and total_pack > 0:
                move.total_dus_pack_str = f"{total_dus} Dus {total_pack} Pack"
            elif total_dus > 0:
                move.total_dus_pack_str = f"{total_dus} Dus"
            else:
                move.total_dus_pack_str = f"{total_pack} Pack"
