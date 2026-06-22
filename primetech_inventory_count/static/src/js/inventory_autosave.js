/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, {

    setup() {

        super.setup(...arguments);

        const isInventoryCountSheet =

            this.props?.resModel ===
                "primetech.inventory.count.sheet"

            &&

            this.props?.viewType ===
                "form";

        if (!isInventoryCountSheet) {
            return;
        }

        console.log(
            "PrimeTech Inventory AutoSave activé"
        );

        this._inventoryAutoSave = setInterval(
            async () => {

                try {

                    const root =
                        this.model?.root;

                    if (!root) {
                        return;
                    }

                    // Pas encore enregistré
                    if (!root.resId) {
                        return;
                    }

                    // Rien à sauvegarder
                    if (!root.isDirty) {
                        return;
                    }

                    await root.save();

                    console.log(
                        "Sauvegarde automatique OK",
                        root.resId
                    );

                } catch (error) {

                    console.error(
                        "Erreur AutoSave",
                        error
                    );
                }

            },
            60000
        );
    },

    willUnmount() {

        if (this._inventoryAutoSave) {

            clearInterval(
                this._inventoryAutoSave
            );
        }

        super.willUnmount();
    },
});