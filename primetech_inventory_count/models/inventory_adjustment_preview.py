from odoo import models, fields


class InventoryAdjustmentPreview(models.TransientModel):
    
    _name = "primetech.inventory.adjustment.preview"
    _description = "Prévisualisation Ajustement"

    sheet_id = fields.Many2one(
        "primetech.inventory.count.sheet"
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
        ("excess", "Surplus"),
    ])

    location_difference = fields.Boolean()