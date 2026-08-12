from odoo import models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_action_add_from_catalog_extra_context(self):
        res = super(SaleOrder, self)._get_action_add_from_catalog_extra_context()
        res['product_catalog_digits'] = (16, 0)
        return res

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_action_add_from_catalog_extra_context(self):
        res = super(AccountMove, self)._get_action_add_from_catalog_extra_context()
        res['product_catalog_digits'] = (16, 0)
        return res

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _get_action_add_from_catalog_extra_context(self):
        res = super(PurchaseOrder, self)._get_action_add_from_catalog_extra_context()
        res['product_catalog_digits'] = (16, 0)
        return res
