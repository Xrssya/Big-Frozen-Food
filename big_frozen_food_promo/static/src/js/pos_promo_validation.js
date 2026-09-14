/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";

console.log("[BFF PROMO] pos_promo_validation.js loaded (v3.0 - PosStore reference fix)");

let currentPosStore = null;

function getPosInstance(entity) {
    if (currentPosStore) return currentPosStore;
    if (entity) {
        if (entity.pos) return entity.pos;
        if (entity.order_id && entity.order_id.pos) return entity.order_id.pos;
        if (entity.env && entity.env.services && entity.env.services.pos) return entity.env.services.pos;
    }
    return null;
}

// ---------------------------------------------------------------------------
// Helper utilities
// ---------------------------------------------------------------------------

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

function getLineQty(line) {
    if (!line) return 0;
    if (typeof line.get_quantity === "function") {
        const q = line.get_quantity();
        if (typeof q === "number" && !isNaN(q)) return q;
    }
    if (typeof line.qty === "number" && !isNaN(line.qty)) return line.qty;
    if (typeof line.quantity === "number" && !isNaN(line.quantity)) return line.quantity;
    return 1;
}

function getAllRecords(model) {
    if (!model) return [];
    if (Array.isArray(model)) return model;
    if (typeof model.getAll === "function") return model.getAll();
    if (typeof model.readAll === "function") return model.readAll();
    if (Array.isArray(model.records)) return model.records;
    if (model.by_id && typeof model.by_id === "object") return Object.values(model.by_id);
    if (model._by_id && typeof model._by_id === "object") return Object.values(model._by_id);
    if (typeof model === "object") {
        const vals = Object.values(model);
        if (vals.length > 0 && typeof vals[0] === "object") return vals;
    }
    return [];
}

function getLineProduct(pos, line) {
    if (!line) return null;
    let prod = line.product_id;
    if (typeof line.get_product === "function") {
        prod = line.get_product();
    } else if (!prod && line.product) {
        prod = line.product;
    }
    if (typeof prod === "number" || typeof prod === "string") {
        const prodId = extractId(prod);
        const pInstance = pos || getPosInstance(line);
        if (pInstance && pInstance.models && pInstance.models["product.product"]) {
            const productModel = pInstance.models["product.product"];
            if (typeof productModel.get === "function") {
                const found = productModel.get(prodId);
                if (found) return found;
            }
            const all = getAllRecords(productModel);
            const found = all.find((p) => extractId(p.id) === prodId);
            if (found) return found;
        }
    }
    return prod;
}

function getPromoModel(posOrOrder) {
    const pos = getPosInstance(posOrOrder);
    if (pos && pos.models && pos.models["product.discount.promo"]) {
        return pos.models["product.discount.promo"];
    }
    if (posOrOrder && posOrOrder.models && posOrOrder.models["product.discount.promo"]) {
        return posOrOrder.models["product.discount.promo"];
    }
    return null;
}

/** Ambil semua promo aktif */
function getActivePromos(pos, order) {
    const promoModel = getPromoModel(pos) || getPromoModel(order);
    let promos = getAllRecords(promoModel);
    const now = new Date();
    const active = promos.filter((p) => {
        if (p.active === false) return false;
        const dStart = parseOdooDate(p.date_start);
        const dEnd = parseOdooDate(p.date_end);
        if (dStart && dStart > now) return false;
        if (dEnd && dEnd < now) return false;
        return true;
    });
    return active;
}

/**
 * Cek apakah sebuah orderline adalah trigger (produk yang memenuhi syarat promo).
 * Baris bonus otomatis (_auto_promo_bonus) TIDAK dihitung sebagai trigger.
 */
function isLineTrigger(pos, line, promo, promoProductIds) {
    if (line._auto_promo_bonus) return false;
    const product = getLineProduct(pos, line);
    if (!product || typeof product !== "object") return false;

    const productId = extractId(product.id);
    const productTmplId = extractId(product.product_tmpl_id) || productId;
    const categId = extractId(product.categ_id);

    if (promo.apply_on === "all") return true;
    if (promo.apply_on === "product") {
        return promoProductIds.includes(productTmplId) || promoProductIds.includes(productId);
    }
    if (promo.apply_on === "category" && categId && promo.category_id) {
        return categId === extractId(promo.category_id);
    }
    return false;
}

/** Cari produk di katalog POS berdasarkan product.template ID atau product.product ID */
function findProductByTmplId(pos, tmplId) {
    const pInstance = getPosInstance(pos);
    if (!tmplId || !pInstance || !pInstance.models) return null;
    const productModel = pInstance.models["product.product"];
    if (!productModel) return null;
    const products = getAllRecords(productModel);

    for (const p of products) {
        const pTmplId = extractId(p.product_tmpl_id);
        const pId = extractId(p.id);
        if (pTmplId === tmplId || pId === tmplId) return p;
    }
    return null;
}

/** Hapus orderline dari order (support berbagai versi API Odoo) */
function removeOrderLine(order, line) {
    if (typeof order.removeOrderline === "function") {
        order.removeOrderline(line);
    } else if (typeof order.remove_orderline === "function") {
        order.remove_orderline(line);
    } else if (order.lines && Array.isArray(order.lines)) {
        const idx = order.lines.indexOf(line);
        if (idx !== -1) order.lines.splice(idx, 1);
    }
}

// ---------------------------------------------------------------------------
// Patch PosStore
// ---------------------------------------------------------------------------

patch(PosStore.prototype, {
    setup() {
        const res = super.setup ? super.setup(...arguments) : undefined;
        currentPosStore = this;
        console.log("[BFF PROMO] PosStore initialized and registered in currentPosStore.");
        return res;
    },

    async addLineToOrder(vals, order, opts = {}, configure = true) {
        currentPosStore = this;
        const res = await super.addLineToOrder(...arguments);
        const targetOrder = order || this.get_order();
        if (targetOrder) {
            this.recomputePromoDiscounts(targetOrder);
            if (!this._isAddingPromoBonus) {
                await this._applyPromoBonus(targetOrder);
            }
        }
        return res;
    },

    async addLineToCurrentOrder(vals, opts = {}, configure = true) {
        currentPosStore = this;
        const res = super.addLineToCurrentOrder ? await super.addLineToCurrentOrder(...arguments) : undefined;
        const currentOrder = this.get_order();
        if (currentOrder) {
            this.recomputePromoDiscounts(currentOrder);
            if (!this._isAddingPromoBonus) {
                await this._applyPromoBonus(currentOrder);
            }
        }
        return res;
    },

    recomputePromoDiscounts(order) {
        currentPosStore = this;
        if (!order || !order.lines || this._isRecomputingPromos) return;
        this._isRecomputingPromos = true;

        try {
            const activePromos = getActivePromos(this, order);
            if (activePromos.length === 0) return;

            for (const line of order.lines) {
                if (line._auto_promo_bonus) continue;
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
                const promoProductIds = (promo.product_ids || []).map((p) => extractId(p));
                const rewardId = extractId(promo.reward_product_id);

                if (promo.promo_type === "discount") {
                    for (const line of order.lines) {
                        if (line._auto_promo_bonus) continue;
                        const product = getLineProduct(this, line);
                        if (!product) continue;
                        const productTmplId =
                            extractId(product.product_tmpl_id) || extractId(product.id);
                        const productId = extractId(product.id);
                        const categId = extractId(product.categ_id);

                        let isMatch = false;
                        if (promo.apply_on === "all") {
                            isMatch = true;
                        } else if (promo.apply_on === "product") {
                            isMatch =
                                promoProductIds.includes(productTmplId) ||
                                promoProductIds.includes(productId);
                        } else if (promo.apply_on === "category" && categId && promo.category_id) {
                            if (categId === extractId(promo.category_id)) isMatch = true;
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
                } else if (promo.promo_type === "buy_x_get_y" && rewardId) {
                    for (const line of order.lines) {
                        if (line._auto_promo_bonus !== promo.id) continue;
                        if (typeof line.set_discount === "function") {
                            line.set_discount(100);
                        } else {
                            line.discount = 100;
                        }
                    }
                }
            }

            for (const line of order.lines) {
                if (line._auto_promo_bonus) continue;
                const product = getLineProduct(this, line);
                if (product && product.is_near_expiry && product.auto_clearance_promo) {
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
    },

    async _applyPromoBonus(order) {
        currentPosStore = this;
        if (!order || !order.lines || this._isAddingPromoBonus) return;
        this._isAddingPromoBonus = true;

        try {
            const activePromos = getActivePromos(this, order);

            for (const promo of activePromos) {
                if (promo.promo_type !== "buy_x_get_y") continue;

                const promoProductIds = (promo.product_ids || []).map((p) => extractId(p));
                const minBuy = promo.min_qty_buy || 2;
                const freeQty = promo.free_qty || 1;
                const explicitRewardId = extractId(promo.reward_product_id);

                if (explicitRewardId) {
                    let totalTriggerQty = 0;
                    for (const line of order.lines) {
                        if (!isLineTrigger(this, line, promo, promoProductIds)) continue;
                        totalTriggerQty += getLineQty(line);
                    }

                    const sets = Math.floor(totalTriggerQty / minBuy);
                    const bonusQtyNeeded = sets * freeQty;
                    await this._syncBonusLine(order, promo, explicitRewardId, bonusQtyNeeded);
                } else {
                    const triggerGroups = new Map();

                    for (const line of order.lines) {
                        if (!isLineTrigger(this, line, promo, promoProductIds)) continue;
                        const product = getLineProduct(this, line);
                        if (!product) continue;

                        const prodKey = extractId(product.product_tmpl_id) || extractId(product.id);
                        if (!triggerGroups.has(prodKey)) {
                            triggerGroups.set(prodKey, { product, totalQty: 0 });
                        }
                        triggerGroups.get(prodKey).totalQty += getLineQty(line);
                    }

                    for (const [prodKey, group] of triggerGroups.entries()) {
                        const sets = Math.floor(group.totalQty / minBuy);
                        const bonusQtyNeeded = sets * freeQty;
                        const promoSubId = `${promo.id}_${prodKey}`;
                        await this._syncBonusLine(order, promo, prodKey, bonusQtyNeeded, promoSubId);
                    }
                }
            }
        } finally {
            this._isAddingPromoBonus = false;
        }
    },

    async _syncBonusLine(order, promo, rewardId, bonusQtyNeeded, tagId = null) {
        const bonusTag = tagId || promo.id;
        const existingBonusLines = order.lines.filter(
            (l) => l._auto_promo_bonus === bonusTag
        );
        const existingBonusQty = existingBonusLines.reduce(
            (sum, l) => sum + getLineQty(l),
            0
        );

        if (bonusQtyNeeded <= 0) {
            for (const line of [...existingBonusLines]) {
                removeOrderLine(order, line);
            }
            return;
        }

        if (existingBonusQty === bonusQtyNeeded) {
            for (const line of existingBonusLines) {
                if (typeof line.set_discount === "function") line.set_discount(100);
                else line.discount = 100;
            }
            return;
        }

        for (const line of [...existingBonusLines]) {
            removeOrderLine(order, line);
        }

        const rewardProduct = findProductByTmplId(this, rewardId);
        if (!rewardProduct) {
            console.warn(
                `[BFF Promo] Produk reward id=${rewardId} tidak ditemukan di katalog POS.`
            );
            return;
        }

        const addFn = this.addLineToOrder || this.addLineToCurrentOrder;
        if (typeof addFn === "function") {
            await addFn.call(
                this,
                {
                    product_id: rewardProduct,
                    qty: bonusQtyNeeded,
                    price_unit: 0,
                    discount: 100,
                },
                order,
                { merge: false },
                false
            );
        }

        const allLines = order.lines;
        for (let i = allLines.length - 1; i >= 0; i--) {
            const newLine = allLines[i];
            if (newLine._auto_promo_bonus) continue;
            const prod = getLineProduct(this, newLine);
            const pTmplId = extractId(prod?.product_tmpl_id) || extractId(prod?.id);
            const pId = extractId(prod?.id);
            if (pTmplId === rewardId || pId === rewardId) {
                newLine._auto_promo_bonus = bonusTag;
                if (typeof newLine.set_discount === "function") newLine.set_discount(100);
                else newLine.discount = 100;
                if (typeof newLine.set_unit_price === "function") newLine.set_unit_price(0);
                else newLine.price = 0;
                break;
            }
        }
    },
});

// ---------------------------------------------------------------------------
// Patch PosOrder — recompute saat data order diperbarui sistem
// ---------------------------------------------------------------------------

patch(PosOrder.prototype, {
    recomputeOrderData() {
        const res = super.recomputeOrderData(...arguments);
        const pos = getPosInstance(this);
        if (pos && typeof pos.recomputePromoDiscounts === "function") {
            pos.recomputePromoDiscounts(this);
        }
        return res;
    },
    set_orderline_quantity(line, quantity) {
        const res = super.set_orderline_quantity ? super.set_orderline_quantity(...arguments) : undefined;
        const pos = getPosInstance(this);
        if (pos && !pos._isAddingPromoBonus) {
            if (typeof pos.recomputePromoDiscounts === "function") {
                pos.recomputePromoDiscounts(this);
            }
            if (typeof pos._applyPromoBonus === "function") {
                Promise.resolve().then(() => {
                    if (!pos._isAddingPromoBonus) {
                        pos._applyPromoBonus(this);
                    }
                });
            }
        }
        return res;
    },
    removeOrderline(line) {
        const res = super.removeOrderline ? super.removeOrderline(...arguments) : undefined;
        const pos = getPosInstance(this);
        if (pos && !pos._isAddingPromoBonus) {
            if (typeof pos.recomputePromoDiscounts === "function") {
                pos.recomputePromoDiscounts(this);
            }
            if (typeof pos._applyPromoBonus === "function") {
                Promise.resolve().then(() => {
                    if (!pos._isAddingPromoBonus) {
                        pos._applyPromoBonus(this);
                    }
                });
            }
        }
        return res;
    },
    remove_orderline(line) {
        const res = super.remove_orderline ? super.remove_orderline(...arguments) : undefined;
        const pos = getPosInstance(this);
        if (pos && !pos._isAddingPromoBonus) {
            if (typeof pos.recomputePromoDiscounts === "function") {
                pos.recomputePromoDiscounts(this);
            }
            if (typeof pos._applyPromoBonus === "function") {
                Promise.resolve().then(() => {
                    if (!pos._isAddingPromoBonus) {
                        pos._applyPromoBonus(this);
                    }
                });
            }
        }
        return res;
    },
});

// ---------------------------------------------------------------------------
// Patch PosOrderline — recompute saat qty baris berubah
// ---------------------------------------------------------------------------

patch(PosOrderline.prototype, {
    set_quantity(quantity, keep_price) {
        const res = super.set_quantity ? super.set_quantity(...arguments) : undefined;
        const pos = getPosInstance(this);
        const order = this.order_id || this.order || (pos ? pos.get_order() : null);
        if (pos && order && !pos._isAddingPromoBonus) {
            if (typeof pos.recomputePromoDiscounts === "function") {
                pos.recomputePromoDiscounts(order);
            }
            if (typeof pos._applyPromoBonus === "function") {
                Promise.resolve().then(() => {
                    if (!pos._isAddingPromoBonus) {
                        pos._applyPromoBonus(order);
                    }
                });
            }
        }
        return res;
    },
});
