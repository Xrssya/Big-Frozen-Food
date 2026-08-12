/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";

patch(PosOrderline.prototype, {
    get quantityStr() {
        const qty = this.qty;
        if (Number.isInteger(qty) || Math.abs(qty - Math.round(qty)) < 1e-6) {
            return String(Math.round(qty));
        }
        return super.quantityStr;
    }
});
