import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class BffDashboardComponent extends Component {
    static template = "bff_dashboard.BffDashboardTemplate";

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({
            period: 'month',
            salesView: 'daily',
            loading: true,
            data: null,
        });

        this.salesChartCanvas = useRef("salesChartCanvas");
        this.channelChartCanvas = useRef("channelChartCanvas");

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadData();
        });

        onMounted(() => {
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
            console.error("Failed to load Executive Dashboard data:", err);
        } finally {
            this.state.loading = false;
        }
    }

    async changePeriod(period) {
        if (this.state.period !== period) {
            this.state.period = period;
            await this.loadData();
            this.renderCharts();
        }
    }

    async reloadDashboard() {
        await this.loadData();
        this.renderCharts();
    }

    toggleSalesView(view) {
        this.state.salesView = view;
        this.renderSalesChart();
    }

    renderCharts() {
        if (this.state.loading || !this.state.data) return;
        setTimeout(() => {
            this.renderSalesChart();
            this.renderChannelChart();
        }, 100);
    }

    renderSalesChart() {
        const canvas = this.salesChartCanvas.el;
        if (!canvas) return;

        if (this.salesChartInstance) {
            this.salesChartInstance.destroy();
        }

        const isDaily = this.state.salesView === 'daily';
        const labels = isDaily ? this.state.data.sales.daily_labels : this.state.data.sales.monthly_labels;
        const totalData = isDaily ? this.state.data.sales.daily_total : this.state.data.sales.monthly_revenue;

        const ctx = canvas.getContext('2d');
        this.salesChartInstance = new window.Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: isDaily ? 'Omset Harian (Rp)' : 'Omset Bulanan (Rp)',
                    data: totalData,
                    backgroundColor: 'rgba(30, 60, 114, 0.8)',
                    borderColor: '#1e3c72',
                    borderWidth: 2,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let val = context.raw || 0;
                                return ' Rp ' + val.toLocaleString('id-ID');
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                if (value >= 1000000) {
                                    return 'Rp ' + (value / 1000000).toFixed(1) + ' Jt';
                                }
                                return 'Rp ' + value.toLocaleString('id-ID');
                            }
                        }
                    }
                }
            }
        });
    }

    renderChannelChart() {
        const canvas = this.channelChartCanvas.el;
        if (!canvas) return;

        if (this.channelChartInstance) {
            this.channelChartInstance.destroy();
        }

        const channelData = this.state.data.sales.channel_comparison;
        const ctx = canvas.getContext('2d');
        this.channelChartInstance = new window.Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Agen & Reseller (B2B)', 'POS Toko Retail'],
                datasets: [{
                    data: [channelData.agen_sales, channelData.pos_sales],
                    backgroundColor: ['#1e3c72', '#17a2b8'],
                    borderWidth: 2,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let val = context.raw || 0;
                                return ' Rp ' + val.toLocaleString('id-ID');
                            }
                        }
                    }
                }
            }
        });
    }

    formatCurrency(value) {
        if (value === undefined || value === null) return 'Rp 0';
        return 'Rp ' + Math.round(value).toLocaleString('id-ID');
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
