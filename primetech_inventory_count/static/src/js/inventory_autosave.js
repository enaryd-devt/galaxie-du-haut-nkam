/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, {

    setup() {
        super.setup(...arguments);

        this._inventoryAutoSave = setInterval(() => {

            if (
                this.model &&
                this.model.root &&
                this.model.root.isDirty
            ) {

                this.model.root.save();

            }

        }, 60000);
    },

    willUnmount() {

        if (this._inventoryAutoSave) {
            clearInterval(this._inventoryAutoSave);
        }

        super.willUnmount();
    },
});