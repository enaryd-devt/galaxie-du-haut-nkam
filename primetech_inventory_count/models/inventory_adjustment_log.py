from odoo import models, fields


class InventoryAdjustmentLog(models.Model):
    _name = "primetech.inventory.adjustment.log"
    _description = "Historique des ajustements"
    _order = "id desc"

    sheet_id = fields.Many2one(
        "primetech.inventory.count.sheet",
        string="Feuille"
    )

    line_id = fields.Many2one(
        "primetech.inventory.count.line",
        string="Ligne"
    )

    product_id = fields.Many2one(
        "product.product",
        string="Produit",
        required=True
    )

    lot_id = fields.Many2one(
        "stock.lot",
        string="Lot"
    )

    expiration_date = fields.Date(
        string="Date expiration"
    )

    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Entrepôt"
    )

    location_id = fields.Many2one(
        "stock.location",
        string="Emplacement"
    )

    qty_system = fields.Float(
        string="Qté système"
    )

    qty_counted = fields.Float(
        string="Qté comptée"
    )

    difference = fields.Float(
        string="Écart"
    )

    difference_type = fields.Selection(
        [
            ("equal", "Conforme"),
            ("missing", "Manquant"),
            ("excess", "excess"),
        ]
    )

    counted_by = fields.Many2one(
        "res.users",
        string="Utilisateur"
    )

    adjustment_date = fields.Datetime(
        string="Date ajustement"
    )

    before_qty = fields.Float(
        string="Qté avant"
    )

    after_qty = fields.Float(
        string="Qté après"
    )

    applied = fields.Boolean(
        default=False
    )

    applied_by = fields.Many2one(
        "res.users",
        string="Appliqué par"
    )