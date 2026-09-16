/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

function currentCashier(pos) {
    return pos.get_cashier?.();
}

function employeeIsInAccessGroup(pos, fieldName) {
    const cashier = currentCashier(pos);
    const employees = pos.config?.[fieldName] ?? pos.config?.raw?.[fieldName] ?? [];
    return Boolean(
        cashier &&
            Array.from(employees).some(
                (employee) => (employee.id ?? (Array.isArray(employee) ? employee[0] : employee)) === cashier.id
            )
    );
}

function cashierIsHistoryRestricted(pos) {
    return employeeIsInAccessGroup(pos, "restricted_employee_ids");
}

function cashierIsRefundRestricted(pos) {
    return (
        employeeIsInAccessGroup(pos, "restricted_employee_ids") ||
        employeeIsInAccessGroup(pos, "order_access_employee_ids")
    );
}

function valsLookLikeRefund(vals = {}) {
    const qty = Number(vals.qty ?? 0);
    return Boolean(vals.refunded_orderline_id || qty < 0);
}

patch(PosStore.prototype, {
    primetechIsRestrictedCashier() {
        return cashierIsHistoryRestricted(this);
    },

    primetechIsRefundRestrictedCashier() {
        return cashierIsRefundRestricted(this);
    },

    primetechCanAccessOrderHistory() {
        return !this.primetechIsRestrictedCashier();
    },

    primetechCanRefund() {
        return !this.primetechIsRefundRestrictedCashier();
    },

    primetechShowAccessDenied(body) {
        // Keep this notification independent from the POS dialog service.  The
        // service is still being initialized while the POS data is loading in
        // recent Odoo versions, whereas the Orders menu can be clicked then.
        window.alert(body);
    },

    primetechShowHistoryDenied() {
        this.primetechShowAccessDenied(_t("Vous n'êtes pas autorisé."));
    },

    primetechShowRefundDenied() {
        this.primetechShowAccessDenied(
            _t("Votre profil ne vous permet pas d'effectuer un remboursement.")
        );
    },

    primetechOpenOrders() {
        if (!this.primetechCanAccessOrderHistory()) {
            this.primetechShowHistoryDenied();
            return;
        }
        return this.showScreen("TicketScreen");
    },

    showScreen(name, props) {
        if (name === "TicketScreen" && !this.primetechCanAccessOrderHistory()) {
            this.primetechShowHistoryDenied();
            return;
        }
        return super.showScreen(...arguments);
    },

    // Do not override the TicketScreen data loaders: Odoo expects their native
    // response shape during initialization.  Access is already stopped above.
    async orderDetails(order) {
        if (order?.finalized && !this.primetechCanAccessOrderHistory()) {
            this.primetechShowHistoryDenied();
            return;
        }
        return await super.orderDetails(...arguments);
    },

    async printReceipt(options = {}) {
        const order = options.order || this.get_order();
        const currentOrder = this.get_order();
        if (
            order?.finalized &&
            currentOrder?.uuid !== order.uuid &&
            !this.primetechCanAccessOrderHistory()
        ) {
            this.primetechShowHistoryDenied();
            return false;
        }
        return await super.printReceipt(...arguments);
    },

    async addLineToOrder(vals, order, opts = {}, configure = true) {
        if (valsLookLikeRefund(vals) && !this.primetechCanRefund()) {
            this.primetechShowRefundDenied();
            return;
        }
        return await super.addLineToOrder(vals, order, opts, configure);
    },
});
