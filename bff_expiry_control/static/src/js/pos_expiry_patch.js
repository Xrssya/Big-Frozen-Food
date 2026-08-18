/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";

patch(PosOrderline.prototype, {
    get_discount() {
        const baseDiscount = super.get_discount ? super.get_discount(...arguments) : (this.discount || 0);
        const product = this.product_id || (this.get_product ? this.get_product() : null);

        if (product && product.is_near_expiry && product.auto_clearance_promo) {
            const clearanceDiscount = product.clearance_discount_percent || 25.0;
            return Math.max(baseDiscount, clearanceDiscount);
        }
        return baseDiscount;
    },

    get_discount_str() {
        const disc = this.get_discount();
        if (disc && disc > 0) {
            return Number.isInteger(disc) || Math.abs(disc - Math.round(disc)) < 1e-6
                ? String(Math.round(disc))
                : String(disc);
        }
        return super.get_discount_str ? super.get_discount_str(...arguments) : "";
    }
});
