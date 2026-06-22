from odoo import models, fields

class InventoryAdjustmentPreview(models.TransientModel):
    
    _name = "primetech.inventory.adjustment.preview"
    _description = "Prévisualisation Ajustement"


    sheet_id = fields.Many2one(
        "primetech.inventory.count.sheet",
        required=True,
        ondelete="cascade",
    )

    line_id = fields.Many2one(
        "primetech.inventory.count.line"
    )

    product_id = fields.Many2one(
        "product.product"
    )

    lot_id = fields.Many2one(
        "stock.lot"
    )

    system_location_id = fields.Many2one(
        "stock.location"
    )

    count_location_id = fields.Many2one(
        "stock.location"
    )

    qty_system = fields.Float()

    qty_counted = fields.Float()

    difference = fields.Float()

    difference_type = fields.Selection([
        ("equal", "Conforme"),
        ("missing", "Manquant"),
        ("excess", "excess"),
    ])

    location_difference = fields.Boolean()

    def action_export_from_preview(self):

        self.ensure_one()

        if not self.sheet_id:
            return False

        return self.sheet_id.action_export_to_odoo_inventory()