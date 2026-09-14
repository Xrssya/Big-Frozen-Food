/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { patch } from "@web/core/utils/patch";

export class AddStockPopup extends Component {
    static template = "bff_stock_control.AddStockPopup";
    static components = { Dialog };
    static props = {
        product: Object,
        close: Function,
    };

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.notification = useService("notification");
        const pcsPerBox = this.props.product.pcs_per_box || 12;
        const currentPrice = this.props.product.lst_price ?? this.props.product.price ?? (this.props.product.raw && this.props.product.raw.lst_price) ?? 0;
        
        this.state = useState({
            qtyPcs: 0,
            qtyBox: 0,
            pcsPerBox: pcsPerBox,
            currentPrice: currentPrice,
            newPrice: currentPrice,
            isPriceLocked: true, // Default LOCKED 🔒
            isSubmitting: false,
        });
    }

    togglePriceLock() {
        this.state.isPriceLocked = !this.state.isPriceLocked;
    }

    onPriceChange(ev) {
        const val = parseFloat(ev.target.value) || 0;
        this.state.newPrice = val;
    }

    onQtyBoxChange(ev) {
        const val = parseFloat(ev.target.value) || 0;
        this.state.qtyBox = val;
        this.state.qtyPcs = Math.round(val * this.state.pcsPerBox);
    }

    onQtyPcsChange(ev) {
        const val = parseFloat(ev.target.value) || 0;
        this.state.qtyPcs = val;
        this.state.qtyBox = Number((val / this.state.pcsPerBox).toFixed(2));
    }

    async confirm() {
        const priceToUpdate = (!this.state.isPriceLocked && this.state.newPrice !== this.state.currentPrice) ? this.state.newPrice : null;
        const stockToAdd = this.state.qtyPcs > 0 ? this.state.qtyPcs : 0;

        if (stockToAdd <= 0 && priceToUpdate === null) {
            this.notification.add(_t("Tidak ada perubahan stok maupun harga yang diinput!"), { type: "warning" });
            return;
        }

        this.state.isSubmitting = true;
        try {
            let pickingTypeId = false;
            if (this.pos && this.pos.config && this.pos.config.picking_type_id) {
                if (typeof this.pos.config.picking_type_id === "number") {
                    pickingTypeId = this.pos.config.picking_type_id;
                } else if (Array.isArray(this.pos.config.picking_type_id)) {
                    pickingTypeId = this.pos.config.picking_type_id[0];
                } else if (typeof this.pos.config.picking_type_id === "object") {
                    pickingTypeId = this.pos.config.picking_type_id.id || (this.pos.config.picking_type_id[0]);
                }
            }

            const res = await this.orm.call("product.product", "update_pos_product_stock_and_price", [
                this.props.product.id,
                stockToAdd,
                priceToUpdate,
                pickingTypeId,
            ]);

            if (res && res.success) {
                const targetProduct = (this.pos.models && this.pos.models["product.product"] && this.pos.models["product.product"].get(this.props.product.id)) || this.props.product;

                // 1. Update live product stock in POS memory
                if (res.new_qty_available !== undefined) {
                    this.props.product.qty_available = res.new_qty_available;
                    if (this.props.product.raw) {
                        this.props.product.raw.qty_available = res.new_qty_available;
                    }
                    if (targetProduct) {
                        targetProduct.qty_available = res.new_qty_available;
                        if (targetProduct.raw) {
                            targetProduct.raw.qty_available = res.new_qty_available;
                        }
                    }
                }
                
                // 2. Update live product price in POS memory
                if (res.new_price !== undefined) {
                    this.props.product.lst_price = res.new_price;
                    this.props.product.price = res.new_price;
                    if (this.props.product.raw) {
                        this.props.product.raw.lst_price = res.new_price;
                        this.props.product.raw.price = res.new_price;
                    }
                    if (targetProduct) {
                        targetProduct.lst_price = res.new_price;
                        targetProduct.price = res.new_price;
                        if (targetProduct.raw) {
                            targetProduct.raw.lst_price = res.new_price;
                            targetProduct.raw.price = res.new_price;
                        }
                    }
                }

                this.notification.add(res.message, { type: "success" });
                this.props.close();
            }
        } catch (error) {
            console.error("Error updating stock/price:", error);
            const msg = error && error.data && error.data.message ? error.data.message : (error.message || String(error));
            this.notification.add(_t("Gagal memperbarui data: ") + msg, { type: "danger" });
        } finally {
            this.state.isSubmitting = false;
        }
    }
}

patch(ProductCard.prototype, {
    setup() {
        super.setup();
        try {
            this.pos = usePos();
        } catch (e) {
            // Context without pos service
        }
        this.dialog = useService("dialog");
    },

    get isAdmin() {
        if (!this.pos) {
            return true;
        }
        if (this.pos._cached_is_admin !== undefined) {
            return this.pos._cached_is_admin;
        }
        const cashier = this.pos.get_cashier ? this.pos.get_cashier() : this.pos.user;
        const role = (cashier && (cashier._role || cashier.role || (cashier.raw && cashier.raw.role))) ||
                     (this.pos.user && (this.pos.user._role || this.pos.user.role || (this.pos.user.raw && this.pos.user.raw.role)));
        
        let res = true;
        if (role === "manager") {
            res = true;
        } else if (this.pos.user && (this.pos.user.id === 2 || this.pos.user.id === 1 || this.pos.user.is_admin || this.pos.user.role === "manager")) {
            res = true;
        } else {
            const cashierName = (cashier && cashier.name) || (this.pos.user && this.pos.user.name) || "";
            if (cashierName && (cashierName.toLowerCase().includes("admin") || cashierName.toLowerCase().includes("administrator"))) {
                res = true;
            }
        }
        this.pos._cached_is_admin = res;
        return res;
    },

    getProductQty() {
        if (!this.props.product) {
            return 0;
        }
        const qty = this.props.product.qty_available ?? (this.props.product.raw && this.props.product.raw.qty_available) ?? 0;
        return typeof qty === "number" ? qty : parseFloat(qty) || 0;
    },

    onAddStockClick(ev) {
        if (ev && ev.stopPropagation) {
            ev.stopPropagation();
        }
        if (!this.isAdmin) {
            return;
        }
        this.dialog.add(AddStockPopup, {
            product: this.props.product,
        });
    }
});
