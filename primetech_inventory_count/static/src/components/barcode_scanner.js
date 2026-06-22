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

        const saved =
            await this.saveForm();

        if (!saved) {

            this.notification.add(
                "Impossible d'enregistrer la feuille.",
                {
                    type: "danger",
                }
            );

            return;
        }

        const barcode =
            (ev.target.value || "").trim();

        if (!barcode) {
            return;
        }

        const path =
            window.location.pathname;

        console.log("PATH =", path);

        let sheetId = false;

        const match =
            path.match(/\/(\d+)$/);

        if (match) {

            sheetId =
                parseInt(match[1]);
        }

        console.log(
            "SHEET ID =",
            sheetId
        );

        console.log(
            "SHEET ID =",
            sheetId
        );

        console.log(
            "BARCODE =",
            barcode
        );

        if (!sheetId) {

            try {

                const saveBtn =
                    document.querySelector(
                        ".o_form_button_save"
                    );

                if (saveBtn) {

                    saveBtn.click();

                    this.notification.add(
                        "Feuille enregistrée, rescanner le produit.",
                        {
                            type: "success",
                        }
                    );

                    setTimeout(() => {

                        location.reload();

                    }, 1000);
                }

            } catch (error) {

                console.error(error);
            }

            return;
        }

        try {

            const result =
                await this.orm.call(
                    "primetech.inventory.count.sheet",
                    "action_scan_barcode",
                    [
                        [sheetId],
                        barcode
                    ]
                );

            console.log(
                "RESULT =",
                result
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

        const list =
            document.querySelector(
                ".o_field_x2many[name='line_ids']"
            );

        if (this.env.model?.root) {

            await this.env.model.root.load();
        }

        setTimeout(() => {

            const input =
                document.querySelector(
                    ".pt_barcode_input"
                );

            if (input) {
                input.focus();
            }

        }, 300);
    }

        } catch (error) {

            console.error(
                "ERREUR COMPLETE",
                error
            );

            console.error(
                "DATA",
                error?.data
            );

            console.error(
                "DEBUG",
                error?.data?.debug
            );

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

    async onAddLine() {

        const saved =
            await this.saveForm();

        if (!saved) {

            this.notification.add(
                "Impossible d'enregistrer la feuille.",
                {
                    type: "danger",
                }
            );

            return;
        }

        const addButton =
            document.querySelector(
                ".o_field_x2many_list_row_add a"
            );

        if (!addButton) {

            this.notification.add(
                "Impossible d'ajouter une ligne.",
                {
                    type: "warning",
                }
            );

            return;
        }

        addButton.click();

        this.notification.add(
            "Nouvelle ligne ajoutée",
            {
                type: "success",
            }
        );

        setTimeout(() => {

            const firstInput =
                document.querySelector(
                    ".o_list_view tbody tr:first-child input"
                );

            if (firstInput) {
                firstInput.focus();
            }

        }, 200);
    }

    async saveForm() {

        try {

            const saveButton =
                document.querySelector(
                    ".o_form_button_save"
                );

            if (saveButton) {

                saveButton.click();

                await new Promise(
                    resolve => setTimeout(
                        resolve,
                        800
                    )
                );
            }

            return true;

        } catch (error) {

            console.error(error);

            return false;
        }
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