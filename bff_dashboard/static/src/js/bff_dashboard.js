/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, onPatched, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

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
        if (this.props.action?.context?.default_mode) {
            defaultMode = this.props.action.context.default_mode;
        } else if (this.props.action?.tag) {
            const tagMap = {
                bff_dashboard_sales: "sales",
                bff_dashboard_stock: "stock",
                bff_dashboard_purchase: "purchase",
            };
            defaultMode = tagMap[this.props.action.tag] || "all";
        }

        this.state = useState({
            mode: defaultMode,
            period: "month",
            salesView: "daily",
            loading: true,
            data: null,
        });

        this.salesChartCanvas = useRef("salesChartCanvas");
        this.channelChartCanvas = useRef("channelChartCanvas");
        this.supplierChartCanvas = useRef("supplierChartCanvas");

        this.salesChartInstance = null;
        this.channelChartInstance = null;
        this.supplierChartInstance = null;

        onWillStart(async () => {
            await this.loadData();
        });

        onMounted(() => {
            this.renderCharts();
        });

        onPatched(() => {
            this.renderCharts();
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            const data = await this.orm.call(
                "bff.dashboard.api",
                "get_dashboard_data",
                [this.state.period]
            );
            this.state.data = data;
        } catch (err) {
            console.error("BFF Dashboard: Failed to load data:", err);
            this.state.data = null;
        } finally {
            this.state.loading = false;
        }
    }

    async changePeriod(period) {
        if (this.state.period !== period) {
            this.state.period = period;
            this.destroyCharts();
            await this.loadData();
        }
    }

    changeMode(mode) {
        this.destroyCharts();
        this.state.mode = mode;
    }

    async reloadDashboard() {
        this.destroyCharts();
        await this.loadData();
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
        }
    }

    destroyCharts() {
        ["sales", "channel", "supplier"].forEach((t) => this.destroyChartInstance(t));
    }

    renderCharts() {
        if (this.state.loading || !this.state.data) return;
        const mode = this.state.mode;
        if (mode === "all" || mode === "sales") {
            this.renderSalesChart();
            this.renderChannelChart();
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

        const isDaily = this.state.salesView === "daily";
        const labels = isDaily
            ? this.state.data.sales.daily_labels
            : this.state.data.sales.monthly_labels;
        const values = isDaily
            ? this.state.data.sales.daily_total
            : this.state.data.sales.monthly_revenue;

        const ctx = canvas.getContext("2d");
        const gradient = ctx.createLinearGradient(0, 0, 0, 260);
        gradient.addColorStop(0, "rgba(37, 99, 235, 0.28)");
        gradient.addColorStop(1, "rgba(37, 99, 235, 0.0)");

        this.salesChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels || [],
                datasets: [
                    {
                        label: isDaily ? "Omset Harian (Rp)" : "Omset Bulanan (Rp)",
                        data: values || [],
                        borderColor: "#2563eb",
                        borderWidth: 2.5,
                        backgroundColor: gradient,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: "#2563eb",
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
