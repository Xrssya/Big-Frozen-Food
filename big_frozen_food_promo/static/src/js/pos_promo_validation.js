import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

function extractId(val) {
    if (!val) return null;
    if (typeof val === "number") return val;
    if (Array.isArray(val)) return val[0];
    if (typeof val === "object" && val.id) return val.id;
    return val;
}

patch(PosStore.prototype, {
    async addLineToOrder(vals, order, opts = {}, configure = true) {
        const res = await super.addLineToOrder(vals, order, opts, configure);
        const currentOrder = order || this.get_order();
        if (currentOrder) {
            this.recomputePromoDiscounts(currentOrder);
        }
        return res;
    },

    recomputePromoDiscounts(order) {
        if (!order || !order.lines) return;

        const promoModel = this.models ? this.models["product.discount.promo"] : null;
        let promos = [];
        if (promoModel) {
            if (typeof promoModel.getAll === "function") {
                promos = promoModel.getAll();
            } else if (typeof promoModel.readAll === "function") {
                promos = promoModel.readAll();
            } else if (Array.isArray(promoModel)) {
                promos = promoModel;
            }
        }

        if (!promos || promos.length === 0) return;

        const now = new Date();

        // Filter active promos by date
        const activePromos = promos.filter(p => {
            if (p.active === false) return false;
            if (p.date_start && new Date(p.date_start) > now) return false;
            if (p.date_end && new Date(p.date_end) < now) return false;
            return true;
        });

        if (activePromos.length === 0) return;

        // Reset auto-applied promo discounts before recalculating
        for (const line of order.lines) {
            if (line._auto_promo_applied) {
                line.set_discount(0);
                line._auto_promo_applied = false;
            }
        }

        for (const promo of activePromos) {
            const promoProductIds = (promo.product_ids || []).map(p => extractId(p));

            if (promo.promo_type === "discount") {
                // Regular percentage/fixed discount
                for (const line of order.lines) {
                    if (!line.product_id) continue;
                    const product = line.product_id;
                    const productTmplId = extractId(product.product_tmpl_id) || extractId(product.id);
                    const productId = extractId(product.id);
                    const categId = extractId(product.categ_id);

                    let isMatch = false;
                    if (promo.apply_on === "all") {
                        isMatch = true;
                    } else if (promo.apply_on === "product") {
                        isMatch = promoProductIds.includes(productTmplId) || promoProductIds.includes(productId);
                    } else if (promo.apply_on === "category" && categId && promo.category_id) {
                        const promoCategId = extractId(promo.category_id);
                        if (categId === promoCategId) isMatch = true;
                    }

                    if (isMatch && (line.get_discount() === 0 || line._auto_promo_applied)) {
                        let discPct = 0;
                        if (promo.discount_type === "percentage") {
                            discPct = promo.discount_value || 0;
                        } else if (promo.discount_type === "fixed" && line.price > 0) {
                            discPct = ((promo.discount_value || 0) / line.price) * 100;
                        }
                        if (discPct > 0 && line.set_discount) {
                            line.set_discount(discPct);
                            line._auto_promo_applied = true;
                        }
                    }
                }
            } else if (promo.promo_type === "buy_x_get_y") {
                const minBuy = promo.min_qty_buy || 2;
                const freeQty = promo.free_qty || 1;
                const rewardTmplId = extractId(promo.reward_product_id);

                // Find total trigger quantity in order lines matching apply_on
                let totalTriggerQty = 0;
                for (const line of order.lines) {
                    if (!line.product_id) continue;
                    const product = line.product_id;
                    const productTmplId = extractId(product.product_tmpl_id) || extractId(product.id);
                    const productId = extractId(product.id);
                    const categId = extractId(product.categ_id);

                    let isMatch = false;
                    if (promo.apply_on === "all") {
                        isMatch = true;
                    } else if (promo.apply_on === "product") {
                        isMatch = promoProductIds.includes(productTmplId) || promoProductIds.includes(productId);
                    } else if (promo.apply_on === "category" && categId && promo.category_id) {
                        const promoCategId = extractId(promo.category_id);
                        if (categId === promoCategId) isMatch = true;
                    }

                    if (isMatch) {
                        totalTriggerQty += (line.get_quantity ? line.get_quantity() : (line.qty || 1));
                    }
                }

                if (rewardTmplId) {
                    // CASE A: BEDA PRODUK HADIAH (reward_product_id IS SET)
                    // Beli X Bakso Ayam, Gratis Y Bakso Sapi Halus
                    if (totalTriggerQty >= minBuy) {
                        const sets = Math.floor(totalTriggerQty / minBuy);
                        const earnedFreeRewardQty = sets * freeQty;

                        for (const line of order.lines) {
                            if (!line.product_id) continue;
                            const product = line.product_id;
                            const productTmplId = extractId(product.product_tmpl_id) || extractId(product.id);
                            const productId = extractId(product.id);

                            if (productTmplId === rewardTmplId || productId === rewardTmplId) {
                                const rewardLineQty = line.get_quantity ? line.get_quantity() : (line.qty || 1);
                                if (rewardLineQty > 0) {
                                    const freeItemsOnLine = Math.min(rewardLineQty, earnedFreeRewardQty);
                                    const discPct = (freeItemsOnLine / rewardLineQty) * 100;
                                    line.set_discount(discPct);
                                    line._auto_promo_applied = true;
                                }
                            }
                        }
                    }
                } else {
                    // CASE B: PRODUK SAMA HADIAH (reward_product_id IS NOT SET)
                    // Beli 2 Gratis 1 (Package size = 3)
                    const packageSize = minBuy + freeQty;
                    for (const line of order.lines) {
                        if (!line.product_id) continue;
                        const product = line.product_id;
                        const productTmplId = extractId(product.product_tmpl_id) || extractId(product.id);
                        const productId = extractId(product.id);
                        const categId = extractId(product.categ_id);

                        let isMatch = false;
                        if (promo.apply_on === "all") {
                            isMatch = true;
                        } else if (promo.apply_on === "product") {
                            isMatch = promoProductIds.includes(productTmplId) || promoProductIds.includes(productId);
                        } else if (promo.apply_on === "category" && categId && promo.category_id) {
                            const promoCategId = extractId(promo.category_id);
                            if (categId === promoCategId) isMatch = true;
                        }

                        if (isMatch) {
                            const qty = line.get_quantity ? line.get_quantity() : (line.qty || 1);
                            if (packageSize > 0 && qty >= packageSize) {
                                const sets = Math.floor(qty / packageSize);
                                const totalFree = sets * freeQty;
                                const discPct = (totalFree / qty) * 100;
                                line.set_discount(discPct);
                                line._auto_promo_applied = true;
                            }
                        }
                    }
                }
            }
        }
    }
});
