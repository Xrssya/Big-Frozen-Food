# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class StockLot(models.Model):
    _inherit = 'stock.lot'

    days_to_expiry = fields.Integer(
        string='Sisa Hari Kadaluarsa',
        compute='_compute_days_to_expiry',
        store=False,
        help='Jumlah sisa hari sebelum tanggal kadaluarsa.'
    )

    expiry_status = fields.Selection([
        ('safe', 'Aman'),
        ('near_expiry', 'Mendekati Expired (Cuci Gudang)'),
        ('expired', 'Kadaluarsa')
    ], string='Status Expiry Lot', compute='_compute_days_to_expiry', store=False)

    @api.depends('expiration_date', 'product_id')
    def _compute_days_to_expiry(self):
        today = fields.Date.today()
        for lot in self:
            if not lot.expiration_date:
                lot.days_to_expiry = 9999
                lot.expiry_status = 'safe'
                continue

            exp_date = fields.Date.to_date(lot.expiration_date)
            diff = (exp_date - today).days
            lot.days_to_expiry = diff

            alert_days = lot.product_id.near_expiry_alert_days or 30
            if diff <= 0:
                lot.expiry_status = 'expired'
            elif diff <= alert_days:
                lot.expiry_status = 'near_expiry'
            else:
                lot.expiry_status = 'safe'

    @api.model
    def get_fefo_lot_recommendation(self, product_id, location_id=False):
        """Returns the recommended FEFO lot for a given product based on earliest expiration_date"""
        domain = [('product_id', '=', product_id), ('expiration_date', '!=', False)]
        lots = self.search(domain, order='expiration_date asc', limit=1)
        return lots.id if lots else False
