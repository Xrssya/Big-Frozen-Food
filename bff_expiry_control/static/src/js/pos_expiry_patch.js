/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Orderline } from "@point_of_sale/app/store/models";

patch(Orderline.prototype, {
    get_discount() {
        const baseDiscount = super.get_discount ? super.get_discount(...arguments) : 0;
        const product = this.get_product();

        if (product && product.is_near_expiry && product.auto_clearance_promo) {
            const clearanceDiscount = product.clearance_discount_percent || 25.0;
            return Math.max(baseDiscount, clearanceDiscount);
        }
        return baseDiscount;
    }
});
