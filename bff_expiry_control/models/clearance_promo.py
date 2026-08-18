# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductDiscountPromo(models.Model):
    _inherit = 'product.discount.promo'

    is_clearance_promo = fields.Boolean(
        string='Promo Cuci Gudang (Near-Expiry)',
        default=False,
        help='Indikator bahwa promo ini diisi secara otomatis oleh sistem untuk produk mendekati kadaluarsa.'
    )

    @api.model
    def sync_near_expiry_clearance_promo(self):
        """Cron & method to sync near-expiry products to clearance promo"""
        PromoObj = self.env['product.discount.promo']
        ProductTmplObj = self.env['product.template']

        # Find near-expiry products
        near_expiry_products = ProductTmplObj.search([
            ('is_storable', '=', True),
            ('auto_clearance_promo', '=', True)
        ]).filtered(lambda p: p.is_near_expiry)

        clearance_promo = PromoObj.search([('is_clearance_promo', '=', True)], limit=1)

        if not clearance_promo:
            clearance_promo = PromoObj.create({
                'name': '🔥 Clearance Sale - Promo Cuci Gudang (Near Expiry)',
                'code': 'CLEARANCE30',
                'promo_type': 'discount',
                'discount_type': 'percentage',
                'discount_value': 25.0,
                'apply_on': 'product',
                'is_clearance_promo': True,
                'notes': 'Promo diskon otomatis untuk produk mendekati tanggal kadaluarsa (FEFO / Clearance Sale).',
                'product_ids': [(6, 0, near_expiry_products.ids)] if near_expiry_products else []
            })
        else:
            clearance_promo.write({
                'active': True if near_expiry_products else False,
                'product_ids': [(6, 0, near_expiry_products.ids)] if near_expiry_products else []
            })

        return True
