/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";

patch(ControlButtons.prototype, {
    clickRefund() {
        if (!this.pos.primetechCanRefund()) {
            this.pos.primetechShowRefundDenied();
            return;
        }
        return super.clickRefund(...arguments);
    },
});

patch(TicketScreen.prototype, {
    async onDoRefund() {
        if (!this.pos.primetechCanRefund()) {
            this.pos.primetechShowRefundDenied();
            return;
        }
        return await super.onDoRefund(...arguments);
    },

    _onUpdateSelectedOrderline() {
        if (!this.pos.primetechCanRefund()) {
            this.numberBuffer.reset();
            this.pos.primetechShowRefundDenied();
            return;
        }
        return super._onUpdateSelectedOrderline(...arguments);
    },

    getHasItemsToRefund() {
        if (!this.pos.primetechCanRefund()) {
            return false;
        }
        return super.getHasItemsToRefund(...arguments);
    },

    async _fetchSyncedOrders() {
        if (!this.pos.primetechCanAccessOrderHistory()) {
            this.pos.primetechShowHistoryDenied();
            return;
        }
        return await super._fetchSyncedOrders(...arguments);
    },

    async onSearch() {
        if (!this.pos.primetechCanAccessOrderHistory()) {
            this.pos.primetechShowHistoryDenied();
            return;
        }
        return await super.onSearch(...arguments);
    },

    async onFilterSelected() {
        if (!this.pos.primetechCanAccessOrderHistory()) {
            this.pos.primetechShowHistoryDenied();
            return;
        }
        return await super.onFilterSelected(...arguments);
    },

    onClickOrder(clickedOrder) {
        if (clickedOrder?.finalized && !this.pos.primetechCanAccessOrderHistory()) {
            this.pos.primetechShowHistoryDenied();
            return;
        }
        return super.onClickOrder(...arguments);
    },

    async _setOrder(order) {
        if (order?.finalized && !this.pos.primetechCanAccessOrderHistory()) {
            this.pos.primetechShowHistoryDenied();
            return;
        }
        return await super._setOrder(...arguments);
    },

    async print(order) {
        if (order?.finalized && !this.pos.primetechCanAccessOrderHistory()) {
            this.pos.primetechShowHistoryDenied();
            return;
        }
        return await super.print(...arguments);
    },
});
