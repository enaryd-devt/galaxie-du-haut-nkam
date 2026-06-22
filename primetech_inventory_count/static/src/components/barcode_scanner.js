/** @odoo-module **/

import { Component, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class BarcodeScanner extends Component {

    static template =
        "primetech_inventory_count.BarcodeScanner";

    setup() {

        this.orm =
            useService("orm");

        this.notification =
            useService("notification");

        this.barcodeInput =
            useRef("barcodeInput");
    }

    async onKeyDown(ev) {

        if (ev.key !== "Enter") {
            return;
        }

        ev.preventDefault();

        const barcode =
            ev.target.value.trim();

        if (!barcode) {
            return;
        }

        const form =
            document.querySelector(".o_form_view");

        const resId =
            parseInt(
                form.dataset.resId
            );

        try {

            const result =
                await this.orm.call(
                    "primetech.inventory.count.sheet",
                    "action_scan_barcode",
                    [
                        [resId],
                        barcode
                    ]
                );

            if (!result.success) {

                this.notification.add(
                    result.message,
                    {
                        type: "warning",
                    }
                );

            } else {

                this.notification.add(
                    result.product_name,
                    {
                        type: "success",
                    }
                );

                location.reload();
            }

        } catch (error) {

            console.error("ERREUR COMPLETE", error);

            if (error.data) {
                console.error("DATA", error.data);
            }

            if (error.message) {
                console.error("MESSAGE", error.message);
            }

            this.notification.add(
                "Erreur lors du scan",
                {
                    type: "danger",
                }
            );
        }

        ev.target.value = "";

        setTimeout(() => {

            ev.target.focus();

        }, 100);
    }
}

registry.category(
    "view_widgets"
).add(
    "primetech_barcode_scanner",
    {
        component: BarcodeScanner,
    }
);