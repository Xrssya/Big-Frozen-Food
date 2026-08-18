/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";

function extractId(val) {
    if (val === null || val === undefined || val === false) return null;
    if (typeof val === "number") return val;
    if (typeof val === "string") {
        if (/^\d+$/.test(val)) return parseInt(val, 10);
        if (val.includes("_")) {
            const parts = val.split("_");
            const last = parts[parts.length - 1];
            if (/^\d+$/.test(last)) return parseInt(last, 10);
        }
    }
    if (Array.isArray(val)) return extractId(val[0]);
    if (typeof val === "object") {
        if (val.id !== undefined) return extractId(val.id);
        if (val.raw && val.raw.id !== undefined) return extractId(val.raw.id);
    }
    return val;
}

function parseOdooDate(str) {
    if (!str) return null;
    if (str instanceof Date) return str;
    if (typeof str === "string") {
        const isoStr = str.includes("T") ? str : str.replace(" ", "T") + "Z";
        const d = new Date(isoStr);
        return isNaN(d.getTime()) ? null : d;
    }
    return null;
}

function getPromoModel(posOrOrder) {
    if (!posOrOrder) return null;
    if (posOrOrder.models && posOrOrder.models["product.discount.promo"]) {
        return posOrOrder.models["product.discount.promo"];
    }
    if (posOrOrder.data && posOrOrder.data.models && posOrOrder.data.models["product.discount.promo"]) {
        return posOrOrder.data.models["product.discount.promo"];
    }
    if (posOrOrder.pos) {
        return getPromoModel(posOrOrder.pos);
    }
    return null;
}

patch(PosStore.prototype, {
    async addLineToCurrentOrder(vals, opts = {}, configure = true) {
        const res = await super.addLineToCurrentOrder(...arguments);
        const currentOrder = this.get_order();
        if (currentOrder) {
            this.recomputePromoDiscounts(currentOrder);
        }
        return res;
    },

    recomputePromoDiscounts(order) {
        if (!order || !order.lines || this._isRecomputingPromos) return;
        this._isRecomputingPromos = true;

        try {
            const promoModel = getPromoModel(this) || getPromoModel(order);
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
            const activePromos = promos.filter(p => {
                if (p.active === false) return false;
                const dStart = parseOdooDate(p.date_start);
                const dEnd = parseOdooDate(p.date_end);
                if (dStart && dStart > now) return false;
                if (dEnd && dEnd < now) return false;
                return true;
            });

            if (activePromos.length === 0) return;

            // Reset auto-applied promo discounts before recalculating
            for (const line of order.lines) {
                if (line._auto_promo_applied) {
                    if (typeof line.set_discount === "function") {
                        line.set_discount(0);
                    } else {
                        line.discount = 0;
                    }
                    line._auto_promo_applied = false;
                }
            }

            for (const promo of activePromos) {
                const promoProductIds = (promo.product_ids || []).map(p => extractId(p));

                if (promo.promo_type === "discount") {
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

                        const currentDisc = line.discount || 0;
                        if (isMatch && (currentDisc === 0 || line._auto_promo_applied)) {
                            let discPct = 0;
                            if (promo.discount_type === "percentage") {
                                discPct = promo.discount_value || 0;
                            } else if (promo.discount_type === "fixed" && line.price > 0) {
                                discPct = ((promo.discount_value || 0) / line.price) * 100;
                            }
                            if (product.is_near_expiry && product.auto_clearance_promo) {
                                const clearanceDisc = product.clearance_discount_percent || 25.0;
                                discPct = Math.max(discPct, clearanceDisc);
                            }
                            if (discPct > 0) {
                                if (typeof line.set_discount === "function") {
                                    line.set_discount(discPct);
                                } else {
                                    line.discount = discPct;
                                }
                                line._auto_promo_applied = true;
                            }
                        }
                    }
                } else if (promo.promo_type === "buy_x_get_y") {
                    const minBuy = promo.min_qty_buy || 2;
                    const freeQty = promo.free_qty || 1;
                    const rewardId = extractId(promo.reward_product_id);

                    // Check if reward product is the same as the buy/trigger product
                    let isSameRewardProduct = false;
                    if (!rewardId) {
                        isSameRewardProduct = true;
                    } else if (promo.apply_on === "product" && promoProductIds.includes(rewardId)) {
                        isSameRewardProduct = true;
                    }

                    if (isSameRewardProduct) {
                        // Scenario A: Same product reward (e.g. Beli 2 Bakso Ayam, Gratis 1 Bakso Ayam)
                        const packageSize = minBuy + freeQty;
                        let totalQty = 0;
                        const matchingLines = [];

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
                                const lineQty = line.get_quantity ? line.get_quantity() : (line.qty || 1);
                                totalQty += lineQty;
                                matchingLines.push({ line, qty: lineQty });
                            }
                        }

                        if (packageSize > 0 && totalQty >= packageSize) {
                            const sets = Math.floor(totalQty / packageSize);
                            let freeQtyToDistribute = sets * freeQty;

                            // Distribute free items starting from last added lines (or smaller lines)
                            const reversedLines = [...matchingLines].reverse();
                            for (const item of reversedLines) {
                                if (freeQtyToDistribute <= 0) break;
                                const freeOnThisLine = Math.min(item.qty, freeQtyToDistribute);
                                const discPct = (freeOnThisLine / item.qty) * 100;
                                if (typeof item.line.set_discount === "function") {
                                    item.line.set_discount(discPct);
                                } else {
                                    item.line.discount = discPct;
                                }
                                item.line._auto_promo_applied = true;
                                freeQtyToDistribute -= freeOnThisLine;
                            }
                        }
                    } else {
                        // Scenario B: Different product reward (e.g. Beli 2 Bakso Ayam, Gratis 1 Sosis Ayam)
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

                        if (totalTriggerQty >= minBuy) {
                            const sets = Math.floor(totalTriggerQty / minBuy);
                            let freeQtyToDistribute = sets * freeQty;

                            // Collect reward lines
                            const rewardLines = [];
                            for (const line of order.lines) {
                                if (!line.product_id) continue;
                                const product = line.product_id;
                                const productTmplId = extractId(product.product_tmpl_id) || extractId(product.id);
                                const productId = extractId(product.id);

                                if (productTmplId === rewardId || productId === rewardId) {
                                    const lineQty = line.get_quantity ? line.get_quantity() : (line.qty || 1);
                                    rewardLines.push({ line, qty: lineQty });
                                }
                            }

                            const reversedRewardLines = [...rewardLines].reverse();
                            for (const item of reversedRewardLines) {
                                if (freeQtyToDistribute <= 0) break;
                                const freeOnThisLine = Math.min(item.qty, freeQtyToDistribute);
                                const discPct = (freeOnThisLine / item.qty) * 100;
                                if (typeof item.line.set_discount === "function") {
                                    item.line.set_discount(discPct);
                                } else {
                                    item.line.discount = discPct;
                                }
                                item.line._auto_promo_applied = true;
                                freeQtyToDistribute -= freeOnThisLine;
                            }
                        }
                    }
                }
            }
            // Ensure near-expiry products get clearance discount if not already higher
            for (const line of order.lines) {
                if (!line.product_id) continue;
                const product = line.product_id;
                if (product.is_near_expiry && product.auto_clearance_promo) {
                    const clearanceDisc = product.clearance_discount_percent || 25.0;
                    if ((line.discount || 0) < clearanceDisc) {
                        if (typeof line.set_discount === "function") {
                            line.set_discount(clearanceDisc);
                        } else {
                            line.discount = clearanceDisc;
                        }
                        line._auto_promo_applied = true;
                    }
                }
            }
        } finally {
            this._isRecomputingPromos = false;
        }
    }
});

patch(PosOrder.prototype, {
    recomputeOrderData() {
        const res = super.recomputeOrderData(...arguments);
        const pos = this.pos || this.models?.pos || (this.models ? this.models["pos.config"]?.getFirst()?.pos : null);
        if (pos && typeof pos.recomputePromoDiscounts === "function") {
            pos.recomputePromoDiscounts(this);
        }
        return res;
    }
});

patch(PosOrderline.prototype, {
    set_quantity(quantity, keep_price) {
        const res = super.set_quantity(...arguments);
        if (this.order_id && this.order_id.pos && typeof this.order_id.pos.recomputePromoDiscounts === "function") {
            this.order_id.pos.recomputePromoDiscounts(this.order_id);
        }
        return res;
    }
});
