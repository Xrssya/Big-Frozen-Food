# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shelf_life_days = fields.Integer(
        string='Masa Simpan / Shelf Life (Hari)',
        default=180,
        help='Estimasi total hari kelayakan konsumsi produk frozen food sejak tanggal produksi.'
    )

    near_expiry_alert_days = fields.Integer(
        string='Ambang Peringatan Kadaluarsa (Hari)',
        default=30,
        help='Batas hari sebelum kadaluarsa untuk memicu peringatan stok mendekati expired (Near-Expiry Alert).'
    )

    auto_clearance_promo = fields.Boolean(
        string='Otomatis Diskon Cuci Gudang',
        default=True,
        help='Jika diaktifkan, produk yang mendekati kadaluarsa akan otomatis dimasukkan ke promo Diskon Cuci Gudang.'
    )

    clearance_discount_percent = fields.Float(
        string='Diskon Cuci Gudang (%)',
        default=25.0,
        digits=(16, 0),
        help='Persentase potongan harga untuk produk yang masuk dalam kategori cuci gudang (Near-Expiry Clearance Sale).'
    )

    is_near_expiry = fields.Boolean(
        string='Mendekati Kadaluarsa',
        compute='_compute_expiry_info',
        search='_search_is_near_expiry',
        help='True jika terdapat stok yang akan kadaluarsa dalam batas ambang hari peringatan.'
    )

    expiry_status = fields.Selection([
        ('safe', 'Kadaluarsa Aman'),
        ('near_expiry', 'Mendekati Expired (Cuci Gudang)'),
        ('expired', 'Kadaluarsa / Expired')
    ], string='Status Kadaluarsa', compute='_compute_expiry_info', search='_search_expiry_status', store=False)

    earliest_expiry_date = fields.Date(
        string='Kadaluarsa Terdekat',
        compute='_compute_expiry_info',
        help='Tanggal kadaluarsa paling dekat dari lot/batch stok fisik yang tersedia.'
    )

    @api.depends('near_expiry_alert_days')
    def _compute_expiry_info(self):
        today = fields.Date.today()
        for template in self:
            lots = self.env['stock.lot'].search([
                ('product_id.product_tmpl_id', '=', template.id),
                ('expiration_date', '!=', False)
            ], order='expiration_date asc')

            if not lots:
                template.is_near_expiry = False
                template.expiry_status = 'safe'
                template.earliest_expiry_date = False
                continue

            earliest_lot = lots[0]
            exp_date = fields.Date.to_date(earliest_lot.expiration_date)
            template.earliest_expiry_date = exp_date

            if exp_date <= today:
                template.expiry_status = 'expired'
                template.is_near_expiry = True
            else:
                days_left = (exp_date - today).days
                if days_left <= template.near_expiry_alert_days:
                    template.expiry_status = 'near_expiry'
                    template.is_near_expiry = True
                else:
                    template.expiry_status = 'safe'
                    template.is_near_expiry = False

    def _search_is_near_expiry(self, operator, value):
        if operator not in ('=', '!='):
            return []
        templates = self.search([])
        matched_ids = [t.id for t in templates if (t.is_near_expiry and value) or (not t.is_near_expiry and not value)]
        return [('id', 'in', matched_ids)]

    def _search_expiry_status(self, operator, value):
        if operator not in ('=', '!='):
            return []
        templates = self.search([])
        matched_ids = [t.id for t in templates if (operator == '=' and t.expiry_status == value) or (operator == '!=' and t.expiry_status != value)]
        return [('id', 'in', matched_ids)]


class ProductProduct(models.Model):
    _inherit = 'product.product'

    shelf_life_days = fields.Integer(related='product_tmpl_id.shelf_life_days', readonly=False, store=True)
    near_expiry_alert_days = fields.Integer(related='product_tmpl_id.near_expiry_alert_days', readonly=False, store=True)
    auto_clearance_promo = fields.Boolean(related='product_tmpl_id.auto_clearance_promo', readonly=False, store=True)
    clearance_discount_percent = fields.Float(related='product_tmpl_id.clearance_discount_percent', readonly=False, store=True)
    is_near_expiry = fields.Boolean(related='product_tmpl_id.is_near_expiry', store=False)
    expiry_status = fields.Selection(related='product_tmpl_id.expiry_status', store=False)
    earliest_expiry_date = fields.Date(related='product_tmpl_id.earliest_expiry_date', store=False)

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields_list = super()._load_pos_data_fields(config_id)
        for field_name in [
            'shelf_life_days', 'near_expiry_alert_days', 'auto_clearance_promo',
            'clearance_discount_percent', 'is_near_expiry', 'expiry_status', 'earliest_expiry_date'
        ]:
            if field_name not in fields_list:
                fields_list.append(field_name)
        return fields_list
