# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    min_stock_alert_qty = fields.Float(
        string='Batas Stok Minimum (Alert)',
        default=10.0,
        help='Batas jumlah stok minimum di mana sistem akan memberikan notifikasi stok menipis.',
        digits=(16, 0)
    )

    min_stock_reserve_qty = fields.Float(
        string='Batas Stok Tahan (Minimum Penjualan)',
        default=0.0,
        help='Batas jumlah stok fisik minimum yang harus tersisa di gudang. Transaksi akan diblokir jika sisa stok kurang dari nilai ini.',
        digits=(16, 0)
    )

    allow_negative_stock = fields.Boolean(
        string='Izinkan Stok Minus',
        default=False,
        help='Jika diaktifkan, produk ini tetap dapat dijual meskipun stok di tangan habis/0.'
    )

    is_low_stock = fields.Boolean(
        string='Stok Menipis',
        compute='_compute_is_low_stock',
        search='_search_is_low_stock',
        help='True jika jumlah stok fisik di tangan (qty_available) kurang dari atau sama dengan batas stok minimum.'
    )

    stock_status = fields.Selection([
        ('available', 'Stok Cukup'),
        ('low', 'Stok Menipis'),
        ('empty', 'Stok Habis')
    ], string='Status Stok', compute='_compute_stock_status', search='_search_stock_status', store=False)

    @api.depends('qty_available', 'min_stock_alert_qty', 'min_stock_reserve_qty', 'is_storable')
    def _compute_stock_status(self):
        for template in self:
            if not template.is_storable:
                template.stock_status = 'available'
            elif template.qty_available <= template.min_stock_reserve_qty:
                template.stock_status = 'empty'
            elif template.qty_available <= template.min_stock_alert_qty:
                template.stock_status = 'low'
            else:
                template.stock_status = 'available'

    def _search_stock_status(self, operator, value):
        if operator not in ('=', '!='):
            return []
        
        templates = self.search([])
        matched_ids = []
        for t in templates:
            status = t.stock_status
            if (operator == '=' and status == value) or (operator == '!=' and status != value):
                matched_ids.append(t.id)
        return [('id', 'in', matched_ids)]

    @api.depends('qty_available', 'min_stock_alert_qty')
    def _compute_is_low_stock(self):
        for template in self:
            template.is_low_stock = (template.qty_available <= template.min_stock_alert_qty)

    def _search_is_low_stock(self, operator, value):
        if operator not in ('=', '!='):
            return []
        templates = self.search([])
        low_stock_ids = [t.id for t in templates if (t.qty_available <= t.min_stock_alert_qty and value) or (t.qty_available > t.min_stock_alert_qty and not value)]
        return [('id', 'in', low_stock_ids)]


class ProductProduct(models.Model):
    _inherit = 'product.product'

    min_stock_alert_qty = fields.Float(
        related='product_tmpl_id.min_stock_alert_qty',
        readonly=False,
        store=True
    )
    min_stock_reserve_qty = fields.Float(
        related='product_tmpl_id.min_stock_reserve_qty',
        readonly=False,
        store=True
    )
    allow_negative_stock = fields.Boolean(
        related='product_tmpl_id.allow_negative_stock',
        readonly=False,
        store=True
    )
    is_low_stock = fields.Boolean(
        related='product_tmpl_id.is_low_stock',
        store=False
    )
    stock_status = fields.Selection(
        related='product_tmpl_id.stock_status',
        store=False
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields_list = super()._load_pos_data_fields(config_id)
        for field_name in ['qty_available', 'min_stock_alert_qty', 'min_stock_reserve_qty', 'is_low_stock', 'stock_status', 'allow_negative_stock']:
            if field_name not in fields_list:
                fields_list.append(field_name)
        return fields_list

