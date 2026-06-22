from odoo import models, fields
from odoo.exceptions import UserError


class InventoryApplyWizard(models.TransientModel):
    _name = "primetech.inventory.apply.wizard"
    _description = "Assistant application inventaire"

    sheet_id = fields.Many2one(
        "primetech.inventory.count.sheet",
        required=True
    )

    line_ids = fields.Many2many(
        comodel_name="primetech.inventory.count.line",
        relation="primetech_inv_apply_line_rel",
        column1="wizard_id",
        column2="line_id",
        string="Lignes"
    )

    def action_apply(self):

        self.ensure_one()

        if not self.line_ids:
            raise UserError(
                "Aucune ligne sélectionnée."
            )

        self.sheet_id.action_apply_inventory()

        return {
            "type": "ir.actions.act_window_close",
        }
    def action_export_from_preview(self):

        self.ensure_one()

        if not self.sheet_id:
            return False

        return self.sheet_id.action_export_to_odoo_inventory()