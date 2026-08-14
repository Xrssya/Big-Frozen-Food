/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";

patch(PosOrder.prototype, {
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(...arguments);

        // ─── Date & Time ────────────────────────────────────────────
        let dateObj = new Date();
        if (this.date_order) {
            dateObj = new Date(this.date_order);
        }
        const pad2 = (n) => String(n).padStart(2, "0");
        const formatted_date = `${dateObj.getFullYear()}-${pad2(dateObj.getMonth() + 1)}-${pad2(dateObj.getDate())}`;
        const formatted_time = `${pad2(dateObj.getHours())}:${pad2(dateObj.getMinutes())}:${pad2(dateObj.getSeconds())}`;

        // ─── Cashier ────────────────────────────────────────────────
        const cashierObj = typeof this.pos?.get_cashier === "function" ? this.pos.get_cashier() : null;
        const cashier_login = (cashierObj?.login || cashierObj?.name || this.user_id?.name || "").toLowerCase();
        const cashier_name = cashierObj?.name || (typeof this.getCashierName === "function" ? this.getCashierName() : "") || "";

        // ─── Partner / Customer ──────────────────────────────────────
        const partner = typeof this.get_partner === "function" ? this.get_partner() : null;
        const customer_name = partner ? partner.name : "";
        let customer_address = "";
        if (partner) {
            customer_address = [partner.street, partner.city].filter(Boolean).join(", ");
        }

        // ─── Order reference / tracking ─────────────────────────────
        let order_ref = this.pos_reference || this.name || "";
        let tracking_number = this.tracking_number || "";
        if (!tracking_number && this.sequence_number) {
            tracking_number = `0-${this.sequence_number}`;
        } else if (!tracking_number) {
            tracking_number = order_ref;
        }
        if (tracking_number && !tracking_number.startsWith("No.")) {
            tracking_number = `No.${tracking_number}`;
        }

        // Barcode-style ref code (digits only)
        const ref_code = (this.pos_reference || this.ticket_code || this.name || "").replace(/[^0-9]/g, "") || order_ref;
        const ticket_code = this.ticket_code || this.name || "";
        const e_receipt_url = `com/e-receipt/${ticket_code || "S-00D39U-07G344G"}`;

        // ─── Orderlines enrichment ────────────────────────────────────
        const orderlines_raw = typeof this.get_orderlines === "function" ? this.get_orderlines() : [];
        let total_qty = 0;

        const enriched_lines = (result.orderlines || []).map((line, index) => {
            const orig = orderlines_raw[index];

            // Quantity
            const rawQty = orig && typeof orig.get_quantity === "function"
                ? orig.get_quantity()
                : parseFloat(line.qty || 0);
            total_qty += rawQty;
            const qty_str = (Number.isInteger(rawQty) || Math.abs(rawQty - Math.round(rawQty)) < 1e-6)
                ? String(Math.round(rawQty))
                : String(rawQty);

            // Unit of measure (skip generic names)
            const GENERIC_UOM = ["units", "unit", "pcs", "piece", "pieces"];
            let unit_name = line.unit || "";
            if (orig?.product_id?.uom_id?.name) {
                const uomName = orig.product_id.uom_id.name;
                unit_name = GENERIC_UOM.includes(uomName.toLowerCase()) ? "" : uomName;
            } else if (GENERIC_UOM.includes(unit_name.toLowerCase())) {
                unit_name = "";
            }

            // Unit price as plain number for formatCurrency in template
            const unit_price_num = orig && typeof orig.get_unit_display_price === "function"
                ? (orig.get_unit_display_price() || 0)
                : (typeof line.unitPrice === "number" ? line.unitPrice : 0);

            // Line total as plain number
            let line_total_num = 0;
            if (typeof line.price === "number") {
                line_total_num = line.price;
            } else if (orig && typeof orig.get_price_with_tax === "function") {
                line_total_num = orig.get_price_with_tax() || 0;
            }

            // Legacy string fallback (only if number not available)
            const price_display = typeof line.price === "string" ? line.price : null;

            return {
                ...line,
                qty_str,
                unit_name,
                unit_price_num,
                line_total_num,
                price_display,
            };
        });

        // ─── Safe numbers for totals ─────────────────────────────────
        const amount_total_num = typeof result.amount_total === "number"
            ? result.amount_total
            : (typeof this.get_total_with_tax === "function" ? (this.get_total_with_tax() || 0) : 0);

        const total_without_tax_num = typeof result.total_without_tax === "number"
            ? result.total_without_tax
            : (typeof this.get_total_without_tax === "function" ? (this.get_total_without_tax() || amount_total_num) : amount_total_num);

        const change_num = typeof result.order_change === "number"
            ? result.order_change
            : (typeof result.change === "number" ? result.change : 0);

        const total_qty_final = (Number.isInteger(total_qty) || Math.abs(total_qty - Math.round(total_qty)) < 1e-6)
            ? Math.round(total_qty)
            : total_qty;

        return {
            ...result,
            // Date / time
            formatted_date,
            formatted_time,
            // Cashier
            cashier_login,
            cashier_name,
            // Customer
            customer_name,
            customer_address,
            // Order info
            tracking_number,
            order_ref,
            ref_code,
            e_receipt_url,
            ticket_code,
            // Lines
            orderlines: enriched_lines,
            total_qty: total_qty_final,
            // Totals (safe numbers)
            amount_total_num,
            total_without_tax_num,
            change_num,
            // Header passthrough
            headerData: {
                ...result.headerData,
                ref_code,
                ticket_code,
                company: this.company,
            },
        };
    },
});
