/** @odoo-module **/
import { Component, onMounted, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AccountingDashboard extends Component {
    static props = { "*": true };
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ loading: true, filters: { company_id: "", period: "month", comparison: "previous_period" }, data: {} });
        onWillStart(() => this.loadData());
        onMounted(() => setTimeout(() => this.renderCharts(), 100));
    }

    async loadData() {
        this.state.loading = true;
        this.state.data = await this.orm.call("primetech.accounting.dashboard", "get_overview_data", [this.state.filters]);
        this.state.filters = { ...this.state.filters, ...(this.state.data.filters || {}) };
        this.state.loading = false;
        setTimeout(() => this.renderCharts(), 0);
    }

    async onFilterChange(key, ev) {
        this.state.filters[key] = ev.target.value;
        await this.loadData();
    }

    async onPeriodChange(ev) {
        await this.onFilterChange("period", ev);
    }

    async onCompanyChange(ev) {
        await this.onFilterChange("company_id", ev);
    }

    async onComparisonChange(ev) {
        await this.onFilterChange("comparison", ev);
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

    openInvoices(extraDomain = []) {
        this.openView("Factures clients", "account.move", [...(this.domain.customer_invoices || []), ...extraDomain]);
    }

    openBills(extraDomain = []) {
        this.openView("Factures fournisseurs", "account.move", [...(this.domain.vendor_bills || []), ...extraDomain]);
    }

    openAccounts(extraDomain = []) {
        this.openView("Comptes", "account.account", [...(this.domain.cash_accounts || []), ...extraDomain]);
    }

    openJournalItems(extraDomain = []) {
        this.openView("Écritures comptables", "account.move.line", [...(this.domain.move_lines || []), ...extraDomain]);
    }

    openPartners(ids = []) {
        this.openView("Clients", "res.partner", ids.length ? [["id", "in", ids]] : []);
    }

    openTrialBalance() {
        this.action.doAction("primetech_reporting_center.action_trial_balance_wizard");
    }

    renderCharts() {
        if (typeof Chart === "undefined") return;
        this.renderTreasuryChart();
        this.renderCashChart();
        this.renderAgeChart();
    }

    renderTreasuryChart() {
        const canvas = document.getElementById("accountingTreasuryChart");
        if (!canvas) return;
        const existing = Chart.getChart(canvas);
        if (existing) existing.destroy();
        const rows = this.state.data.treasury_evolution || [];
        new Chart(canvas, { type: "line", data: { labels: rows.map((row) => row.label), datasets: [{ label: "Encaissements", data: rows.map((row) => row.incoming), borderColor: "#2563eb", backgroundColor: "#2563eb", tension: 0.35 }, { label: "Décaissements", data: rows.map((row) => row.outgoing), borderColor: "#ef4444", backgroundColor: "#ef4444", tension: 0.35 }, { label: "Solde cumulé", data: rows.map((row) => row.balance), borderColor: "#16a34a", backgroundColor: "#16a34a", tension: 0.35 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "top", align: "start" } } } });
    }

    renderCashChart() {
        const canvas = document.getElementById("accountingCashChart");
        if (!canvas) return;
        const existing = Chart.getChart(canvas);
        if (existing) existing.destroy();
        const rows = this.state.data.cash_accounts || [];
        new Chart(canvas, { type: "doughnut", data: { labels: rows.map((row) => row.name), datasets: [{ data: rows.map((row) => row.amount), backgroundColor: ["#2563eb", "#16a34a", "#f97316", "#f59e0b"], borderWidth: 0 }] }, options: { responsive: true, maintainAspectRatio: false, cutout: "58%", plugins: { legend: { position: "right", labels: { boxWidth: 10, font: { size: 10 } } } } } });
    }

    renderAgeChart() {
        const canvas = document.getElementById("accountingAgeChart");
        if (!canvas) return;
        const existing = Chart.getChart(canvas);
        if (existing) existing.destroy();
        const rows = this.state.data.receivable_aging || [];
        new Chart(canvas, { type: "doughnut", data: { labels: rows.map((row) => row.label), datasets: [{ data: rows.map((row) => row.amount), backgroundColor: ["#2563eb", "#f59e0b", "#ef4444", "#7c3aed"], borderWidth: 0 }] }, options: { responsive: true, maintainAspectRatio: false, cutout: "58%", plugins: { legend: { position: "right", labels: { boxWidth: 10, font: { size: 10 } } } } } });
    }
}
AccountingDashboard.template = "primetech_reporting_center.AccountingDashboard";
