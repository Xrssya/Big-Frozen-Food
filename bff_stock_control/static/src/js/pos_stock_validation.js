import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PosStore.prototype, {
    async addLineToOrder(vals, order, opts = {}, configure = true) {
        let product = vals.product_id;
        if (typeof product === "number") {
            product = this.models["product.product"].get(product);
        }

        if (product && product.type === "consu" && !product.allow_negative_stock) {
            const availableQty = product.qty_available || 0;
            const minAlertQty = product.min_stock_alert_qty || 10;
            const minReserveQty = product.min_stock_reserve_qty || 0;
            const sellableQty = availableQty - minReserveQty;

            // Calculate current quantity of this product already in current order lines
            let existingQty = 0;
            if (order && order.lines) {
                existingQty = order.lines
                    .filter(line => line.product_id && line.product_id.id === product.id)
                    .reduce((sum, line) => sum + (line.qty || 0), 0);
            }

            const requestedQty = existingQty + (vals.qty || 1);
            const remainingAfterSale = availableQty - requestedQty;

            // 1. Block transaction if sellable stock <= 0 or requested quantity causes remaining stock < minReserveQty
            if (sellableQty <= 0 || requestedQty > sellableQty) {
                this.env.services.dialog.add(AlertDialog, {
                    title: _t("⛔ TRANSAKSI DIBLOKIR: MENCAPAI BATAS STOK TAHAN"),
                    body: _t(
                        `Produk "${product.display_name}" tidak dapat ditambahkan!\n\n` +
                        `• Stok Fisik Tersedia: ${availableQty} unit\n` +
                        `• Batas Minimum Tahan: ${minReserveQty} unit\n` +
                        `• Maksimal Dapat Dijual: ${Math.max(0, sellableQty)} unit\n` +
                        `• Total Permintaan Penjualan: ${requestedQty} unit\n\n` +
                        `Sistem Big Frozen Food memblokir penjualan karena sisa stok tidak boleh kurang dari ${minReserveQty} unit. Silakan lakukan restock produk!`
                    ),
                });
                return false;
            }

            // 2. Display low stock notification if remaining quantity after sale <= minAlertQty
            if (remainingAfterSale <= minAlertQty) {
                this.env.services.notification.add(
                    _t(`⚠️ STOK MENIPIS: "${product.display_name}" tersisa ${remainingAfterSale} pack setelah transaksi ini (Batas alert: ${minAlertQty} pack, Batas tahan: ${minReserveQty} pack)`),
                    { type: "warning", sticky: false }
                );
            }
        }

        return await super.addLineToOrder(vals, order, opts, configure);
    }
});

