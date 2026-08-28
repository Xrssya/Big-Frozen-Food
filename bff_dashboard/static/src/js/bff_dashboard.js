/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, onWillUnmount, onPatched, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class BffDashboardComponent extends Component {
    static template = "bff_dashboard.BffDashboardTemplate";
    static props = {
        action: { type: Object, optional: true },
        "*": true,
    };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");

        let defaultMode = "all";
        let isEmbedded = false;

        if (this.props.action?.context?.default_mode) {
            defaultMode = this.props.action.context.default_mode;
            if (defaultMode !== "all") {
                isEmbedded = true;
            }
        } else if (this.props.action?.tag) {
            const tagMap = {
                bff_dashboard_sales: "sales",
                bff_dashboard_stock: "stock",
                bff_dashboard_purchase: "purchase",
                bff_dashboard_pos: "pos",
            };
            if (tagMap[this.props.action.tag]) {
                defaultMode = tagMap[this.props.action.tag];
                isEmbedded = true;
            }
        }

        const formatDate = (d) => {
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, "0");
            const day = String(d.getDate()).padStart(2, "0");
            return `${year}-${month}-${day}`;
        };

        this.getPresetDates = (preset) => {
            const today = new Date();
            let from = new Date();
            let to = today;

            if (preset === "month") {
                from = new Date(today.getFullYear(), today.getMonth(), 1);
            } else if (preset === "30days") {
                from = new Date();
                from.setDate(today.getDate() - 30);
            } else if (preset === "year") {
                from = new Date(today.getFullYear(), 0, 1);
            } else if (preset === "all") {
                from = new Date(2020, 0, 1);
            }
            return {
                dateFrom: formatDate(from),
                dateTo: formatDate(to),
            };
        };

        const initialDates = this.getPresetDates("month");

        this.state = useState({
            mode: defaultMode,
            isEmbedded: isEmbedded,
            period: "month",
            dateFrom: initialDates.dateFrom,
            dateTo: initialDates.dateTo,
            salesView: "daily",
            companyId: "all",
            selectedDayIdx: null,
            loading: true,
            data: null,
            popularTimesData: null,
            lowStockSort: "stok_asc",
            nearExpirySort: "expiry_asc",
            topProductSort: "revenue_desc",
            topPosProductSort: "revenue_desc",
            purchaseOrderSort: "date_desc",
        });

        this.salesChartCanvas = useRef("salesChartCanvas");
        this.channelChartCanvas = useRef("channelChartCanvas");
        this.supplierChartCanvas = useRef("supplierChartCanvas");
        this.popularTimesCanvas = useRef("popularTimesCanvas");

        this.salesChartInstance = null;
        this.channelChartInstance = null;
        this.supplierChartInstance = null;
        this.popularTimesChartInstance = null;

        this.autoRefreshInterval = null;

        onWillStart(async () => {
            if (!window.Chart) {
                try {
                    await loadJS("/bff_dashboard/static/lib/chart.min.js");
                } catch (e) {
                    console.warn("BFF Dashboard: Failed to load local Chart.js, trying CDN fallback", e);
                    try {
                        await loadJS("https://cdn.jsdelivr.net/npm/chart.js");
                    } catch (e2) {
                        console.error("BFF Dashboard: Failed to load Chart.js from CDN", e2);
                    }
                }
            }
            await this.loadData();
        });

        onMounted(() => {
            this.renderCharts();
            // Live Background Polling every 15 seconds without interrupting UI
            this.autoRefreshInterval = setInterval(() => {
                this.silentReloadData();
            }, 15000);
        });

        onWillUnmount(() => {
            if (this.autoRefreshInterval) {
                clearInterval(this.autoRefreshInterval);
                this.autoRefreshInterval = null;
            }
            this.destroyCharts();
        });

        onPatched(() => {
            setTimeout(() => this.renderCharts(), 50);
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            const [data, popularTimes] = await Promise.all([
                this.orm.call(
                    "bff.dashboard.api",
                    "get_dashboard_data",
                    [this.state.period, this.state.dateFrom, this.state.dateTo, this.state.companyId]
                ),
                this.orm.call(
                    "bff.dashboard.api",
                    "get_popular_times_data",
                    [this.state.companyId, this.state.selectedDayIdx]
                ),
            ]);
            this.state.data = data;
            this.state.popularTimesData = popularTimes;
            if (this.state.selectedDayIdx === null && popularTimes) {
                this.state.selectedDayIdx = popularTimes.selected_day_idx;
            }
        } catch (err) {
            console.error("BFF Dashboard: Failed to load data:", err);
            this.state.data = null;
        } finally {
            this.state.loading = false;
        }
    }

    async loadPopularTimesData() {
        try {
            const popularTimes = await this.orm.call(
                "bff.dashboard.api",
                "get_popular_times_data",
                [this.state.companyId, this.state.selectedDayIdx]
            );
            this.state.popularTimesData = popularTimes;
            if (this.state.selectedDayIdx === null && popularTimes) {
                this.state.selectedDayIdx = popularTimes.selected_day_idx;
            }
        } catch (err) {
            console.error("BFF Dashboard: Failed to load popular times data:", err);
            this.state.popularTimesData = null;
        }
    }

    async onBranchChange(ev) {
        this.state.companyId = ev.target.value;
        this.destroyCharts();
        await this.loadData();
    }

    async onDayChange(ev) {
        this.state.selectedDayIdx = parseInt(ev.target.value, 10);
        await this.loadPopularTimesData();
        this.renderPopularTimesChart();
    }

    async silentReloadData() {
        try {
            const [data, popularTimes] = await Promise.all([
                this.orm.call(
                    "bff.dashboard.api",
                    "get_dashboard_data",
                    [this.state.period, this.state.dateFrom, this.state.dateTo, this.state.companyId]
                ),
                this.orm.call(
                    "bff.dashboard.api",
                    "get_popular_times_data",
                    [this.state.companyId, this.state.selectedDayIdx]
                ),
            ]);
            this.state.data = data;
            this.state.popularTimesData = popularTimes;
            this.renderCharts();
        } catch (err) {
            console.error("BFF Dashboard: Background silent refresh failed:", err);
        }
    }

    async selectPreset(preset) {
        this.state.period = preset;
        const dates = this.getPresetDates(preset);
        this.state.dateFrom = dates.dateFrom;
        this.state.dateTo = dates.dateTo;
        this.destroyCharts();
        await this.loadData();
    }

    onCustomDateFocus() {
        this.state.period = "custom";
    }

    async onCustomDateChange() {
        this.state.period = "custom";
        if (this.state.dateFrom && this.state.dateTo && this.state.dateFrom <= this.state.dateTo) {
            this.destroyCharts();
            await this.loadData();
        }
    }

    changeMode(mode) {
        this.destroyCharts();
        this.state.mode = mode;
    }

    toggleSalesView(view) {
        this.state.salesView = view;
        this.destroyChartInstance("sales");
        this.renderSalesChart();
    }

    destroyChartInstance(type) {
        if (type === "sales" && this.salesChartInstance) {
            this.salesChartInstance.destroy();
            this.salesChartInstance = null;
        } else if (type === "channel" && this.channelChartInstance) {
            this.channelChartInstance.destroy();
            this.channelChartInstance = null;
        } else if (type === "supplier" && this.supplierChartInstance) {
            this.supplierChartInstance.destroy();
            this.supplierChartInstance = null;
        } else if (type === "popularTimes" && this.popularTimesChartInstance) {
            this.popularTimesChartInstance.destroy();
            this.popularTimesChartInstance = null;
        }
    }

    destroyCharts() {
        ["sales", "channel", "supplier", "popularTimes"].forEach((t) => this.destroyChartInstance(t));
    }

    renderCharts() {
        if (this.state.loading || !this.state.data) return;
        const mode = this.state.mode;
        if (mode === "all" || mode === "sales" || mode === "pos") {
            this.renderSalesChart();
            if (mode !== "pos") {
                this.renderChannelChart();
            }
            this.renderPopularTimesChart();
        }
        if (mode === "all" || mode === "purchase") {
            this.renderSupplierChart();
        }
    }

    _getChart() {
        return window.Chart;
    }

    renderSalesChart() {
        const Chart = this._getChart();
        if (!Chart) return;
        const canvas = this.salesChartCanvas.el;
        if (!canvas) return;

        const isPos = this.state.mode === "pos";
        const isDaily = this.state.salesView === "daily";
        
        let labels = [];
        let values = [];
        let chartLabel = "";

        if (isPos) {
            labels = this.state.data.pos.daily_labels || [];
            values = this.state.data.pos.daily_values || [];
            chartLabel = "Omset POS Toko (Rp)";
        } else {
            labels = isDaily ? this.state.data.sales.daily_labels : this.state.data.sales.monthly_labels;
            values = isDaily ? this.state.data.sales.daily_total : this.state.data.sales.monthly_revenue;
            chartLabel = isDaily ? "Omset Harian (Rp)" : "Omset Bulanan (Rp)";
        }

        const lineColor = isPos ? "#06b6d4" : "#2563eb";
        const stopColor = isPos ? "rgba(6, 182, 212, 0.3)" : "rgba(37, 99, 235, 0.28)";

        if (this.salesChartInstance) {
            this.salesChartInstance.data.labels = labels || [];
            this.salesChartInstance.data.datasets[0].label = chartLabel;
            this.salesChartInstance.data.datasets[0].data = values || [];
            this.salesChartInstance.data.datasets[0].borderColor = lineColor;
            this.salesChartInstance.data.datasets[0].pointBackgroundColor = lineColor;
            this.salesChartInstance.update("none");
            return;
        }

        const ctx = canvas.getContext("2d");
        const gradient = ctx.createLinearGradient(0, 0, 0, 260);
        gradient.addColorStop(0, stopColor);
        gradient.addColorStop(1, "rgba(255, 255, 255, 0.0)");

        this.salesChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels || [],
                datasets: [
                    {
                        label: chartLabel,
                        data: values || [],
                        borderColor: lineColor,
                        borderWidth: 2.5,
                        backgroundColor: gradient,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: lineColor,
                        pointBorderColor: "#ffffff",
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 7,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                onHover: (event, chartElement) => {
                    if (event.native && event.native.target) {
                        event.native.target.style.cursor = chartElement && chartElement.length ? "pointer" : "default";
                    }
                },
                onClick: (event, elements) => {
                    if (elements && elements.length > 0) {
                        const idx = elements[0].index;
                        this.onSalesChartPointClick(idx);
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#0f172a",
                        titleFont: { size: 12, weight: "bold" },
                        bodyFont: { size: 13 },
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: (context) => {
                                const idx = context.dataIndex;
                                const val = context.raw || 0;
                                if (this.state.mode === 'pos') {
                                    return "Omset POS Toko: Rp " + val.toLocaleString("id-ID");
                                } else if (this.state.mode === 'sales') {
                                    return "Omset Sales B2B: Rp " + val.toLocaleString("id-ID");
                                } else {
                                    const soVal = (this.state.data?.sales?.daily_so && this.state.data.sales.daily_so[idx]) || 0;
                                    const posVal = (this.state.data?.sales?.daily_pos && this.state.data.sales.daily_pos[idx]) || 0;
                                    return [
                                        "Total Omset: Rp " + val.toLocaleString("id-ID"),
                                        " • B2B Sales: Rp " + soVal.toLocaleString("id-ID"),
                                        " • POS Retail: Rp " + posVal.toLocaleString("id-ID"),
                                    ];
                                }
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: "#64748b", font: { size: 11 } },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: "#f1f5f9" },
                        ticks: {
                            color: "#64748b",
                            font: { size: 11 },
                            callback: (v) =>
                                v >= 1000000
                                    ? "Rp " + (v / 1000000).toFixed(1) + " Jt"
                                    : "Rp " + v.toLocaleString("id-ID"),
                        },
                    },
                },
            },
        });
    }

    onSalesChartPointClick(index) {
        const isPos = this.state.mode === "pos";
        const isDaily = this.state.salesView === "daily";

        if (isPos) {
            const dates = (this.state.data && this.state.data.pos && this.state.data.pos.daily_dates) || [];
            const dateStr = dates[index];
            if (!dateStr) return;
            this.actionService.doAction({
                name: "Transaksi POS Toko (" + dateStr + ")",
                type: "ir.actions.act_window",
                res_model: "pos.order",
                views: [[false, "list"], [false, "form"]],
                domain: [
                    ["state", "in", ["paid", "done", "invoiced"]],
                    ["date_order", ">=", dateStr + " 00:00:00"],
                    ["date_order", "<=", dateStr + " 23:59:59"],
                ],
            });
        } else if (isDaily) {
            const dates = (this.state.data && this.state.data.sales && this.state.data.sales.daily_dates) || [];
            const dateStr = dates[index];
            if (!dateStr) return;

            const soVal = (this.state.data?.sales?.daily_so && this.state.data.sales.daily_so[index]) || 0;
            const posVal = (this.state.data?.sales?.daily_pos && this.state.data.sales.daily_pos[index]) || 0;

            if (this.state.mode === "sales" || (soVal > 0 && posVal === 0)) {
                this.actionService.doAction({
                    name: "Order Penjualan B2B (" + dateStr + ")",
                    type: "ir.actions.act_window",
                    res_model: "sale.order",
                    views: [[false, "list"], [false, "form"]],
                    domain: [
                        ["state", "in", ["sale", "done"]],
                        ["date_order", ">=", dateStr + " 00:00:00"],
                        ["date_order", "<=", dateStr + " 23:59:59"],
                    ],
                });
            } else if (soVal === 0 && posVal > 0) {
                this.actionService.doAction({
                    name: "Transaksi POS Toko (" + dateStr + ")",
                    type: "ir.actions.act_window",
                    res_model: "pos.order",
                    views: [[false, "list"], [false, "form"]],
                    domain: [
                        ["state", "in", ["paid", "done", "invoiced"]],
                        ["date_order", ">=", dateStr + " 00:00:00"],
                        ["date_order", "<=", dateStr + " 23:59:59"],
                    ],
                });
            } else {
                this.actionService.doAction({
                    name: "Order Penjualan B2B (" + dateStr + ") - POS Retail: Rp " + posVal.toLocaleString("id-ID"),
                    type: "ir.actions.act_window",
                    res_model: "sale.order",
                    views: [[false, "list"], [false, "form"]],
                    domain: [
                        ["state", "in", ["sale", "done"]],
                        ["date_order", ">=", dateStr + " 00:00:00"],
                        ["date_order", "<=", dateStr + " 23:59:59"],
                    ],
                });
            }
        } else {
            const infoList = (this.state.data && this.state.data.sales && this.state.data.sales.monthly_info) || [];
            const info = infoList[index];
            if (!info) return;
            this.actionService.doAction({
                name: "Order Penjualan (" + info.label + ")",
                type: "ir.actions.act_window",
                res_model: "sale.order",
                views: [[false, "list"], [false, "form"]],
                domain: [
                    ["state", "in", ["sale", "done"]],
                    ["date_order", ">=", info.start],
                    ["date_order", "<=", info.end],
                ],
            });
        }
    }

    renderChannelChart() {
        const Chart = this._getChart();
        if (!Chart) return;
        const canvas = this.channelChartCanvas.el;
        if (!canvas) return;

        const ch = this.state.data.sales.channel_comparison || {};

        if (this.channelChartInstance) {
            this.channelChartInstance.data.datasets[0].data = [ch.agen_sales || 0, ch.pos_sales || 0];
            this.channelChartInstance.update("none");
            return;
        }
        this.channelChartInstance = new Chart(canvas.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: ["Agen & Reseller (B2B)", "POS Toko Retail"],
                datasets: [
                    {
                        data: [ch.agen_sales || 0, ch.pos_sales || 0],
                        backgroundColor: ["#2563eb", "#06b6d4"],
                        borderWidth: 3,
                        borderColor: "#ffffff",
                        hoverOffset: 6,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "72%",
                onHover: (event, chartElement) => {
                    if (event.native && event.native.target) {
                        event.native.target.style.cursor = chartElement && chartElement.length ? "pointer" : "default";
                    }
                },
                onClick: (event, elements) => {
                    if (elements && elements.length > 0) {
                        const idx = elements[0].index;
                        if (idx === 0) {
                            this.openSalesAction();
                        } else {
                            this.openPosAction();
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#0f172a",
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: (c) => " Rp " + (c.raw || 0).toLocaleString("id-ID"),
                        },
                    },
                },
            },
        });
    }

    renderSupplierChart() {
        const Chart = this._getChart();
        if (!Chart) return;
        const canvas = this.supplierChartCanvas.el;
        if (!canvas) return;

        const suppliers = this.state.data.purchase.supplier_breakdown || [];

        if (this.supplierChartInstance) {
            this.supplierChartInstance.data.labels = suppliers.map((s) => s.supplier);
            this.supplierChartInstance.data.datasets[0].data = suppliers.map((s) => s.total);
            this.supplierChartInstance.update("none");
            return;
        }
        const ctx = canvas.getContext("2d");

        this.supplierChartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: suppliers.map((s) => s.supplier),
                datasets: [
                    {
                        label: "Total Belanja (Rp)",
                        data: suppliers.map((s) => s.total),
                        backgroundColor: "#6366f1",
                        hoverBackgroundColor: "#4f46e5",
                        borderRadius: 8,
                        borderSkipped: false,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                onHover: (event, chartElement) => {
                    if (event.native && event.native.target) {
                        event.native.target.style.cursor = chartElement && chartElement.length ? "pointer" : "default";
                    }
                },
                onClick: (event, elements) => {
                    if (elements && elements.length > 0) {
                        const idx = elements[0].index;
                        const supp = suppliers[idx];
                        if (supp) {
                            this.openSupplierDetail(supp.partner_id);
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#0f172a",
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: (c) => " Rp " + (c.raw || 0).toLocaleString("id-ID"),
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: "#64748b", font: { size: 11 } },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: "#f1f5f9" },
                        ticks: {
                            color: "#64748b",
                            font: { size: 11 },
                            callback: (v) =>
                                v >= 1000000
                                    ? "Rp " + (v / 1000000).toFixed(1) + " Jt"
                                    : "Rp " + v.toLocaleString("id-ID"),
                        },
                    },
                },
            },
        });
    }

    renderPopularTimesChart() {
        const Chart = this._getChart();
        if (!Chart) return;
        const canvas = this.popularTimesCanvas.el;
        if (!canvas) return;

        const pData = this.state.popularTimesData;
        if (!pData || !pData.hourly_data) return;

        const labels = pData.hourly_data.map((h) => h.label);
        const counts = pData.hourly_data.map((h) => h.count);
        const pcts = pData.hourly_data.map((h) => h.percentage);

        const bgColors = pcts.map((pct) => {
            if (pct >= 85) return "#ef4444";
            if (pct >= 40) return "#06b6d4";
            return "#94a3b8";
        });

        if (this.popularTimesChartInstance) {
            this.popularTimesChartInstance.data.labels = labels;
            this.popularTimesChartInstance.data.datasets[0].data = pcts;
            this.popularTimesChartInstance.data.datasets[0].backgroundColor = bgColors;
            this.popularTimesChartInstance.update("none");
            return;
        }

        const ctx = canvas.getContext("2d");
        this.popularTimesChartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Intensitas Keramaian (%)",
                        data: pcts,
                        backgroundColor: bgColors,
                        borderRadius: 6,
                        borderSkipped: false,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#0f172a",
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: (c) => {
                                const idx = c.dataIndex;
                                const cnt = counts[idx] || 0;
                                return `Keramaian: ${c.raw}% (${cnt} Transaksi)`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: "#64748b", font: { size: 10 } },
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: "#f1f5f9" },
                        ticks: {
                            color: "#64748b",
                            font: { size: 10 },
                            callback: (v) => v + "%",
                        },
                    },
                },
            },
        });
    }

    formatCurrency(value) {
        if (value === undefined || value === null) return "Rp 0";
        return "Rp " + Math.round(value).toLocaleString("id-ID");
    }

    openSalesAction() {
        const ids = (this.state.data && this.state.data.sales && this.state.data.sales.so_ids) || [];
        this.actionService.doAction({
            name: "Order Penjualan (B2B)",
            type: "ir.actions.act_window",
            res_model: "sale.order",
            views: [[false, "list"], [false, "form"]],
            domain: [["id", "in", ids]],
        });
    }

    openPosAction() {
        const ids = (this.state.data && this.state.data.sales && this.state.data.sales.pos_ids) || [];
        this.actionService.doAction({
            name: "Transaksi POS Toko",
            type: "ir.actions.act_window",
            res_model: "pos.order",
            views: [[false, "list"], [false, "form"]],
            domain: [["id", "in", ids]],
        });
    }

    openPosSessionAction() {
        this.actionService.doAction({
            name: "Sesi Kasir POS",
            type: "ir.actions.act_window",
            res_model: "pos.session",
            views: [[false, "list"], [false, "form"]],
            domain: [],
        });
    }

    openStockValueAction() {
        this.actionService.doAction("bff_dashboard.action_bff_stock_valuation_quant");
    }

    openLowStockAction() {
        const ids = (this.state.data && this.state.data.stock && this.state.data.stock.low_stock_ids) || [];
        this.actionService.doAction({
            name: "Stok Menipis (Reorder Alert)",
            type: "ir.actions.act_window",
            res_model: "product.product",
            views: [[false, "list"], [false, "form"]],
            domain: [["id", "in", ids]],
        });
    }

    openExpiryAction() {
        const ids = (this.state.data && this.state.data.stock && this.state.data.stock.near_expiry_ids) || [];
        this.actionService.doAction({
            name: "Stok Near-Expiry (FEFO)",
            type: "ir.actions.act_window",
            res_model: "stock.lot",
            views: [[false, "list"], [false, "form"]],
            domain: [["id", "in", ids]],
        });
    }

    openPurchaseAction() {
        const ids = (this.state.data && this.state.data.purchase && this.state.data.purchase.po_ids) || [];
        this.actionService.doAction({
            name: "Pembelian / Purchase Orders",
            type: "ir.actions.act_window",
            res_model: "purchase.order",
            views: [[false, "list"], [false, "form"]],
            domain: [["id", "in", ids]],
        });
    }

    openPurchaseOrderDetail(poId) {
        if (!poId) return;
        this.actionService.doAction({
            name: "Order Pembelian",
            type: "ir.actions.act_window",
            res_model: "purchase.order",
            res_id: poId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openProductDetail(productId) {
        if (!productId) return;
        this.actionService.doAction({
            name: "Detail Produk",
            type: "ir.actions.act_window",
            res_model: "product.product",
            res_id: productId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openLotDetail(lotId) {
        if (!lotId) return;
        this.actionService.doAction({
            name: "Detail Lot",
            type: "ir.actions.act_window",
            res_model: "stock.lot",
            res_id: lotId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openSupplierDetail(partnerId) {
        if (!partnerId) {
            this.openPurchaseAction();
            return;
        }
        const poIds = (this.state.data && this.state.data.purchase && this.state.data.purchase.po_ids) || [];
        this.actionService.doAction({
            name: "PO Supplier",
            type: "ir.actions.act_window",
            res_model: "purchase.order",
            views: [[false, "list"], [false, "form"]],
            domain: [["partner_id", "=", partnerId], ["id", "in", poIds]],
        });
    }

    get sortedLowStockItems() {
        const items = (this.state.data && this.state.data.stock && this.state.data.stock.low_stock_items) || [];
        const copy = [...items];
        const sort = this.state.lowStockSort;
        if (sort === "stok_asc") {
            copy.sort((a, b) => a.qty_available - b.qty_available);
        } else if (sort === "stok_desc") {
            copy.sort((a, b) => b.qty_available - a.qty_available);
        } else if (sort === "name_asc") {
            copy.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
        } else if (sort === "name_desc") {
            copy.sort((a, b) => (b.name || "").localeCompare(a.name || ""));
        }
        return copy;
    }

    get sortedNearExpiryItems() {
        const items = (this.state.data && this.state.data.stock && this.state.data.stock.near_expiry_items) || [];
        const copy = [...items];
        const sort = this.state.nearExpirySort;
        if (sort === "expiry_asc") {
            copy.sort((a, b) => a.days_left - b.days_left);
        } else if (sort === "expiry_desc") {
            copy.sort((a, b) => b.days_left - a.days_left);
        } else if (sort === "name_asc") {
            copy.sort((a, b) => (a.product_name || "").localeCompare(b.product_name || ""));
        }
        return copy;
    }

    get sortedTopProducts() {
        const items = (this.state.data && this.state.data.sales && this.state.data.sales.top_5_products) || [];
        const copy = [...items];
        const sort = this.state.topProductSort;
        if (sort === "revenue_desc") {
            copy.sort((a, b) => b.revenue - a.revenue);
        } else if (sort === "qty_desc") {
            copy.sort((a, b) => b.qty - a.qty);
        } else if (sort === "name_asc") {
            copy.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
        }
        return copy;
    }

    get sortedTopPosProducts() {
        const items = (this.state.data && this.state.data.pos && this.state.data.pos.top_5_products) || [];
        const copy = [...items];
        const sort = this.state.topPosProductSort || "revenue_desc";
        if (sort === "revenue_desc") {
            copy.sort((a, b) => b.revenue - a.revenue);
        } else if (sort === "qty_desc") {
            copy.sort((a, b) => b.qty - a.qty);
        } else if (sort === "name_asc") {
            copy.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
        }
        return copy;
    }

    get sortedRecentPurchaseOrders() {
        const items = (this.state.data && this.state.data.purchase && this.state.data.purchase.recent_orders) || [];
        const copy = [...items];
        const sort = this.state.purchaseOrderSort;
        if (sort === "date_desc") {
            // default date desc
        } else if (sort === "date_asc") {
            copy.reverse();
        } else if (sort === "total_desc") {
            copy.sort((a, b) => b.amount_total - a.amount_total);
        } else if (sort === "total_asc") {
            copy.sort((a, b) => a.amount_total - b.amount_total);
        } else if (sort === "vendor_asc") {
            copy.sort((a, b) => (a.partner_name || "").localeCompare(b.partner_name || ""));
        }
        return copy;
    }
}

registry.category("actions").add("bff_dashboard_main", BffDashboardComponent);
registry.category("actions").add("bff_dashboard_sales", BffDashboardComponent);
registry.category("actions").add("bff_dashboard_stock", BffDashboardComponent);
registry.category("actions").add("bff_dashboard_purchase", BffDashboardComponent);
registry.category("actions").add("bff_dashboard_pos", BffDashboardComponent);
