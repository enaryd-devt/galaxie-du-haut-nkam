/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

patch(FormController.prototype, {

    onClickAddInventoryLine() {

        const addButton = document.querySelector(
            ".o_field_x2many_list_row_add"
        );

        if (addButton) {
            addButton.click();
        }
    },
});