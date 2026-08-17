/** @odoo-module **/

import { Component, onMounted, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class SalesOverviewDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ loaded: false, period: "month", data: {} });
        onWillStart(async () => this.refresh());
        onMounted(() => setTimeout(() => this.renderChart(), 100));
    }

    async setPeriod(period) {
        this.state.period = period;
        await this.refresh();
    }

    async refresh() {
        this.state.loaded = false;
        this.state.data = await this.orm.call("primetech.sales.overview", "get_dashboard_data", [{ period: this.state.period }]);
        this.state.loaded = true;
        setTimeout(() => this.renderChart(), 0);
    }

    get domain() {
        return this.state.data.domains || {};
    }

    money(value) {
        return `${Math.round(value || 0).toLocaleString()} FCFA`;
    }

    pct(value) {
        return `${Number(value || 0).toFixed(1)}%`;
    }

    openView(name, resModel, domain = [], views = [[false, "list"], [false, "form"]]) {
        this.action.doAction({ type: "ir.actions.act_window", name, res_model: resModel, views, view_mode: views.map((view) => view[1]).join(","), domain });
    }

    openOrders(extraDomain = []) {
        this.openView("Commandes clients", "sale.order", [...(this.domain.orders || []), ...extraDomain]);
    }

    openInvoices(extraDomain = []) {
        this.openView("Factures clients", "account.move", [...(this.domain.invoices || []), ...extraDomain]);
    }

    openPartners(ids = []) {
        this.openView("Clients", "res.partner", ids.length ? [["id", "in", ids]] : (this.domain.customers || []));
    }

    openProducts(ids = []) {
        this.openView("Produits", "product.product", ids.length ? [["id", "in", ids]] : []);
    }

    openSalespersons(ids = []) {
        this.openView("Commerciaux", "res.users", ids.length ? [["id", "in", ids]] : []);
    }

    renderChart() {
        const canvas = document.getElementById("salesEvolutionChart");
        if (!canvas || !this.state.data.monthly_sales) return;
        if (this.chart) this.chart.destroy();
        const labels = this.state.data.monthly_sales.map((item) => item.month);
        this.chart = new Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [
                    { type: "bar", label: "Chiffre d'affaires (FCFA)", data: this.state.data.monthly_sales.map((item) => item.amount), backgroundColor: "#1d9bf0", borderRadius: 5 },
                    { type: "line", label: "Marge (FCFA)", data: this.state.data.monthly_sales.map((item) => item.margin || 0), borderColor: "#21b573", backgroundColor: "#21b573", tension: 0.35, yAxisID: "y" },
                    { type: "line", label: "Commandes", data: this.state.data.monthly_sales.map((item) => item.orders || 0), borderColor: "#ff9f1c", backgroundColor: "#ff9f1c", tension: 0.35, yAxisID: "y1" },
                ],
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "top", align: "start" } }, scales: { y: { beginAtZero: true }, y1: { beginAtZero: true, position: "right", grid: { drawOnChartArea: false } } } },
        });
    }
}

SalesOverviewDashboard.template = "primetech_reporting_center.SalesOverviewDashboard";
registry.category("actions").add("primetech_sales_overview_dashboard", SalesOverviewDashboard);
