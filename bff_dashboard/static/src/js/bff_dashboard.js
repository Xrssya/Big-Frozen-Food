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
            // Live Background Polling every 30 seconds without interrupting UI
            this.autoRefreshInterval = setInterval(() => {
                this.silentReloadData();
            }, 30000);
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
            const data = await this.orm.call(
                "bff.dashboard.api",
                "get_dashboard_data",
                [this.state.period, this.state.dateFrom, this.state.dateTo, this.state.companyId]
            );
            this.state.data = data;
            await this.loadPopularTimesData();
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
        this.destroyChartInstance("popularTimes");
        await this.loadPopularTimesData();
        this.renderPopularTimesChart();
    }

    async silentReloadData() {
        try {
            const data = await this.orm.call(
                "bff.dashboard.api",
                "get_dashboard_data",
                [this.state.period, this.state.dateFrom, this.state.dateTo, this.state.companyId]
            );
            this.state.data = data;
            await this.loadPopularTimesData();
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

        this.destroyChartInstance("sales");

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

        const ctx = canvas.getContext("2d");
        const gradient = ctx.createLinearGradient(0, 0, 0, 260);
        const lineColor = isPos ? "#06b6d4" : "#2563eb";
        const stopColor = isPos ? "rgba(6, 182, 212, 0.3)" : "rgba(37, 99, 235, 0.28)";

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
                            label: (context) =>
                                "Omset: Rp " + (context.raw || 0).toLocaleString("id-ID"),
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

    renderChannelChart() {
        const Chart = this._getChart();
        if (!Chart) return;
        const canvas = this.channelChartCanvas.el;
        if (!canvas) return;

        this.destroyChartInstance("channel");

        const ch = this.state.data.sales.channel_comparison || {};
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

        this.destroyChartInstance("supplier");

        const suppliers = this.state.data.purchase.supplier_breakdown || [];
        const ctx = canvas.getContext("2d");
        const gradient = ctx.createLinearGradient(0, 0, 0, 260);
        gradient.addColorStop(0, "#818cf8");
        gradient.addColorStop(1, "#4338ca");

        this.supplierChartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: suppliers.map((s) => s.supplier),
                datasets: [
                    {
                        label: "Total Belanja (Rp)",
                        data: suppliers.map((s) => s.total),
                        backgroundColor: gradient,
                        borderRadius: 8,
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

        this.destroyChartInstance("popularTimes");

        const pData = this.state.popularTimesData;
        if (!pData || !pData.hourly_data) return;

        const labels = pData.hourly_data.map((h) => h.label);
        const counts = pData.hourly_data.map((h) => h.count);
        const pcts = pData.hourly_data.map((h) => h.percentage);

        const ctx = canvas.getContext("2d");

        const bgColors = pcts.map((pct) => {
            if (pct >= 85) return "#ef4444";
            if (pct >= 40) return "#06b6d4";
            return "#94a3b8";
        });

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

    openLowStockAction() {
        this.actionService.doAction({
            name: "Stok Menipis",
            type: "ir.actions.act_window",
            res_model: "product.product",
            views: [[false, "list"], [false, "form"]],
            domain: [["is_storable", "=", true]],
        });
    }

    openExpiryAction() {
        this.actionService.doAction({
            name: "Stok Mendekati Expired",
            type: "ir.actions.act_window",
            res_model: "stock.lot",
            views: [[false, "list"], [false, "form"]],
            domain: [],
        });
    }
}

registry.category("actions").add("bff_dashboard_main", BffDashboardComponent);
registry.category("actions").add("bff_dashboard_sales", BffDashboardComponent);
registry.category("actions").add("bff_dashboard_stock", BffDashboardComponent);
registry.category("actions").add("bff_dashboard_purchase", BffDashboardComponent);
registry.category("actions").add("bff_dashboard_pos", BffDashboardComponent);
