# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    installment_count = fields.Integer(
        string="Cicilan Aktif",
        compute="_compute_installment_count",
        help="Jumlah transaksi cicilan pelanggan yang belum lunas."
    )

    def _compute_installment_count(self):
        for partner in self:
            partner.installment_count = self.env['account.move'].search_count([
                ('partner_id', 'child_of', partner.id),
                ('is_installment', '=', True),
                ('installment_status', '=', 'ongoing'),
                ('move_type', '=', 'out_invoice'),
            ])

    def action_view_partner_installments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("bff_pos_cicilan.action_account_move_cicilan")
        action['domain'] = [
            ('partner_id', 'child_of', self.id),
            ('is_installment', '=', True),
            ('move_type', '=', 'out_invoice')
        ]
        action['context'] = {
            'default_partner_id': self.id,
            'search_default_ongoing': 1,
        }
        return action
