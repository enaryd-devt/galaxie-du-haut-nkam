/** @odoo-module **/

import { Component, useState, onMounted, onWillStart, onWillUpdateProps, onWillUnmount } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

export class ExecutiveBoard extends Component {
    static props = { filters: { type: Object, optional: true }, refreshKey: { optional: true }, "*": true };
    setup() {
        this.actionService = useService("action");
        this.stateStorageKey = "primetechExecutiveBoardState";
        this.scrollStorageKey = "primetechExecutiveBoardScroll";
        const savedState = this.loadSavedState();
        const defaultKpiFilters = { cash_period: "today", billing_period: "month", stock_scope: "all", store_period: "week", revenue_period: "week", customer_receivable_filter: "all", supplier_receivable_filter: "all" };
        this.boardCache = new Map();
        this.currentRequestId = 0;
        this.state = useState({ loading: true, period: savedState.period || "today", clockTick: Date.now(), kpiFilters: { ...defaultKpiFilters, ...(savedState.kpiFilters || {}) }, partnerSearch: { customers: "", suppliers: "" }, kpis: [], stores: [], revenue_chart: { subtitle: "Mois en cours", items: [] }, cash: [], banks: [], stock: {}, partner_balance_kpis: { customers: { rows: [] }, suppliers: { rows: [] } }, current_user: { name: "Directeur Général", status: "En ligne" }, alerts: [], quick_actions: [], activities: [], performance: [] });
        onWillStart(async () => this.loadBoard({ force: true }));
        onMounted(() => {
            this.restoreScroll();
            this.scrollListener = () => this.scheduleSaveScroll();
            window.addEventListener("scroll", this.scrollListener, { passive: true });
            this.clockInterval = setInterval(() => {
                this.state.clockTick = Date.now();
            }, 1000);
            this.refreshInterval = setInterval(() => {
                this.loadBoard({ silent: true });
            }, 30000);
        });
        onWillUnmount(() => {
            if (this.clockInterval) {
                clearInterval(this.clockInterval);
            }
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
            if (this.scrollListener) {
                window.removeEventListener("scroll", this.scrollListener);
            }
            if (this.scrollSaveTimeout) {
                clearTimeout(this.scrollSaveTimeout);
            }
            Object.values(this.partnerSearchTimeouts || {}).forEach((timeout) => clearTimeout(timeout));
            this.saveDashboardState();
            this.saveScroll();
        });
        onWillUpdateProps(async (nextProps) => {
            if (nextProps.refreshKey !== this.props.refreshKey) {
                await this.loadBoard();
            }
        });
    }

    getBoardFilters() {
        return {
            ...(this.props.filters || {}),
            period: this.state.period,
            kpi_filters: { ...this.state.kpiFilters },
            partner_search: { ...this.state.partnerSearch },
        };
    }

    getBoardCacheKey(filters = this.getBoardFilters()) {
        return JSON.stringify(filters);
    }

    rememberBoardData(key, data) {
        this.boardCache.set(key, data);
        if (this.boardCache.size > 12) {
            this.boardCache.delete(this.boardCache.keys().next().value);
        }
    }

    applyBoardData(data, options = {}) {
        Object.assign(this.state, data, { loading: false });
        if (options.restoreScroll) {
            this.restoreScroll();
        }
    }

    async loadBoard(options = {}) {
        const filters = this.getBoardFilters();
        const cacheKey = this.getBoardCacheKey(filters);
        const cachedData = this.boardCache.get(cacheKey);
        if (cachedData && !options.force) {
            this.applyBoardData(cachedData, options);
            return;
        }
        if (!options.silent && !this.state.kpis.length) {
            this.state.loading = true;
        }
        const requestId = ++this.currentRequestId;
        const data = await rpc("/web/dataset/call_kw", {
            model: "primetech.dashboard",
            method: "get_executive_board",
            args: [filters],
            kwargs: {},
        });
        this.rememberBoardData(cacheKey, data);
        if (requestId === this.currentRequestId) {
            this.applyBoardData(data, options);
        }
    }

    async onPeriodChange(ev) {
        const nextPeriod = ev.target.value;
        if (nextPeriod === this.state.period) {
            return;
        }
        this.state.period = nextPeriod;
        this.saveDashboardState();
        await this.loadBoard({ silent: true });
    }

    async onKpiFilterChange(key, ev) {
        const nextValue = ev.target.value;
        if (nextValue === this.state.kpiFilters[key]) {
            return;
        }
        this.state.kpiFilters[key] = nextValue;
        this.saveDashboardState();
        await this.loadBoard({ silent: true });
    }

    onPartnerSearchInput(type, ev) {
        this.state.partnerSearch[type] = ev.target.value;
    }

    onPartnerSearchKeydown(type, ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.searchPartner(type);
        }
    }

    async searchPartner(type) {
        if (!this.state.partnerSearch[type].trim()) {
            await this.resetPartnerSearch(type);
            return;
        }
        this.partnerSearchDefaults ||= {};
        if (!this.partnerSearchDefaults[type]) {
            const kpi = this.state.partner_balance_kpis[type];
            this.partnerSearchDefaults[type] = {
                rows: [...(kpi.rows || [])],
                filtered_count: kpi.filtered_count,
            };
        }
        await this.loadPartnerKpis(type);
    }

    resetPartnerSearch(type) {
        this.state.partnerSearch[type] = "";
        const defaults = this.partnerSearchDefaults?.[type];
        if (defaults) {
            const kpi = this.state.partner_balance_kpis[type];
            kpi.rows = [...defaults.rows];
            kpi.filtered_count = defaults.filtered_count;
        }
    }

    async loadPartnerKpis(type) {
        this.partnerSearchRequestIds ||= {};
        const requestId = (this.partnerSearchRequestIds[type] || 0) + 1;
        this.partnerSearchRequestIds[type] = requestId;
        const filters = this.getBoardFilters();
        filters.partner_search_type = type;
        const data = await rpc("/web/dataset/call_kw", {
            model: "primetech.dashboard",
            method: "get_partner_balance_kpis",
            args: [filters],
            kwargs: {},
        });
        if (requestId === this.partnerSearchRequestIds[type]) {
            const currentKpi = this.state.partner_balance_kpis[type];
            currentKpi.rows = data[type].rows;
            currentKpi.filtered_count = data[type].filtered_count;
        }
    }

    loadSavedState() {
        try {
            return JSON.parse(sessionStorage.getItem(this.stateStorageKey) || "{}");
        } catch {
            return {};
        }
    }

    saveDashboardState() {
        sessionStorage.setItem(this.stateStorageKey, JSON.stringify({
            period: this.state.period,
            kpiFilters: this.state.kpiFilters,
        }));
    }

    scheduleSaveScroll() {
        if (this.scrollSaveTimeout) {
            return;
        }
        this.scrollSaveTimeout = setTimeout(() => {
            this.saveScroll();
            this.scrollSaveTimeout = null;
        }, 150);
    }

    saveScroll() {
        sessionStorage.setItem(this.scrollStorageKey, String(window.scrollY || document.documentElement.scrollTop || 0));
    }

    restoreScroll() {
        const savedScroll = Number(sessionStorage.getItem(this.scrollStorageKey) || 0);
        if (savedScroll) {
            requestAnimationFrame(() => {
                window.scrollTo(0, savedScroll);
                setTimeout(() => window.scrollTo(0, savedScroll), 250);
            });
        }
    }

    revenueCurvePoints() {
        const items = this.state.revenue_chart.items || [];
        if (!items.length) return "0,55 100,55";
        const maximum = Math.max(...items.map((item) => Number(item.value) || 0));
        if (!maximum) return "0,55 100,55";
        const last = Math.max(items.length - 1, 1);
        return items.map((item, index) => {
            const ratio = Math.max(0, Math.min((Number(item.value) || 0) / maximum, 1));
            return `${(index / last) * 100},${88 - ratio * 76}`;
        }).join(" ");
    }

    revenueSummary() {
        const values = (this.state.revenue_chart.items || []).map((item) => Number(item.value) || 0);
        const total = values.reduce((sum, value) => sum + value, 0);
        const nonZero = values.filter((value) => value > 0);
        const first = values[0] || 0;
        const last = values[values.length - 1] || 0;
        return { total, max: Math.max(...values, 0), min: nonZero.length ? Math.min(...nonZero) : 0, average: values.length ? total / values.length : 0, trend: first ? ((last - first) / first) * 100 : 0 };
    }

    revenueCurveDots() {
        const items = this.state.revenue_chart.items || [];
        const maximum = Math.max(...items.map((item) => Number(item.value) || 0));
        const last = Math.max(items.length - 1, 1);
        return items.map((item, index) => ({ key: item.key, x: (index / last) * 100, y: maximum ? 88 - ((Number(item.value) || 0) / maximum) * 76 : 55 }));
    }


    revenueCashflowSeries() {
        const items = this.state.revenue_chart.items || [];
        let cumulative = 0;
        return items.map((item, index) => {
            const income = Number(item.income ?? item.incoming ?? item.encaissements ?? item.value) || 0;
            const expense = Number(item.expense ?? item.outgoing ?? item.decaissements) || 0;
            cumulative += income - expense;
            const balance = Number(item.balance ?? item.cumulative ?? item.solde_cumule ?? cumulative) || 0;
            return {
                key: item.key || `${item.label || "point"}-${index}`,
                label: item.label,
                income,
                expense,
                balance,
            };
        });
    }

    revenueChartMaximum() {
        const series = this.revenueCashflowSeries();
        const maximum = Math.max(...series.flatMap((item) => [item.income, item.expense, item.balance]), 0);
        if (!maximum) {
            return 1;
        }
        const magnitude = 10 ** Math.max(Math.floor(Math.log10(maximum)) - 1, 0);
        return Math.ceil(maximum / magnitude) * magnitude;
    }

    revenueSeriesPoints(type) {
        const series = this.revenueCashflowSeries();
        const maximum = this.revenueChartMaximum();
        const last = Math.max(series.length - 1, 1);
        return series.map((item, index) => {
            const value = Math.max(0, Number(item[type]) || 0);
            return {
                key: `${type}-${item.key}`,
                x: (index / last) * 100,
                y: 88 - Math.min(value / maximum, 1) * 80,
            };
        });
    }

    revenueSeriesPath(type) {
        const points = this.revenueSeriesPoints(type);
        if (!points.length) {
            return "M 0 88 L 100 88";
        }
        if (points.length === 1) {
            return `M ${points[0].x} ${points[0].y}`;
        }
        return points.reduce((path, point, index) => {
            if (!index) {
                return `M ${point.x} ${point.y}`;
            }
            const previous = points[index - 1];
            const controlOffset = (point.x - previous.x) * 0.45;
            return `${path} C ${previous.x + controlOffset} ${previous.y}, ${point.x - controlOffset} ${point.y}, ${point.x} ${point.y}`;
        }, "");
    }

    revenueSeriesDots(type) {
        return this.revenueSeriesPoints(type);
    }

    revenueGridLines() {
        const items = this.state.revenue_chart.items || [];
        const last = Math.max(items.length - 1, 1);
        return [0, 1, 2, 3, 4].map((index) => ({
            key: `grid-${index}`,
            y: 8 + index * 20,
            x: items.length ? (index / Math.max(4, last)) * 100 : index * 25,
        }));
    }
    revenueScaleLabels() {
        const maximum = this.revenueChartMaximum();
        return [maximum, maximum * .75, maximum * .5, maximum * .25, 0].map((value, index) => ({ key: `scale-${index}`, label: this.formatCompactAmount(value) }));
    }

    formatCompactAmount(value) {
        return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 }).format(Math.round(value || 0));
    }

    categoryColor(index) {
        return ["#2f80ed", "#16a34a", "#fb923c", "#8b5cf6", "#64748b", "#ef4444"][index % 6];
    }

    categoryDonutStyle() {
        const items = this.state.categories?.items || [];
        if (!items.length) return "background: conic-gradient(#e2e8f0 0 100%)";
        const colors = ["#2f80ed", "#16a34a", "#fb923c", "#8b5cf6", "#ef4444", "#64748b"];
        let cursor = 0;
        const segments = items.map((item, index) => {
            const end = Math.min(cursor + (Number(item.percent) || 0), 100);
            const segment = `${colors[index % colors.length]} ${cursor}% ${end}%`;
            cursor = end;
            return segment;
        });
        return `background: conic-gradient(${segments.join(", ")})`;
    }

    openAction(action) {
        if (action) {
            this.saveDashboardState();
            this.saveScroll();
            this.actionService.doAction(action);
        }
    }

    userInitials() {
        const name = this.state.current_user?.name || "DG";
        return name.split(" ").filter(Boolean).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
    }

    todayLabel() {
        return new Intl.DateTimeFormat("fr-FR", { day: "2-digit", month: "short", year: "numeric" }).format(new Date());
    }

    timeLabel() {
        return new Intl.DateTimeFormat("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(new Date(this.state.clockTick));
    }

    format(value, suffix = "") {
        const amount = new Intl.NumberFormat("fr-FR").format(Math.round(value || 0));
        return suffix ? `${amount} ${suffix}` : amount;
    }

    formatPercent(value) {
        return `${new Intl.NumberFormat("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value || 0)} %`;
    }
}

ExecutiveBoard.template = "primetech_reporting_center.ExecutiveBoard";
