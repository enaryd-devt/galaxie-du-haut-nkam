from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class InventoryCountLine(models.Model):
    _name = "primetech.inventory.count.line"
    _description = "Ligne de comptage"
    _order = "id desc"


    sheet_id = fields.Many2one(
        "primetech.inventory.count.sheet",
        string="Feuille",
        required=True,
        ondelete="cascade",
    )

    product_id = fields.Many2one(
        "product.product",
        string="Produit",
        required=True,
    )

    tracking = fields.Selection(
        related="product_id.tracking",
        string="Suivi",
        store=True,
        readonly=True,
    )

    system_location_id = fields.Many2one(
        "stock.location",
        string="Emplacement système",
    )

    count_location_id = fields.Many2one(
        "stock.location",
        string="Sous-emplacement compté",
    )

    allowed_location_ids = fields.Many2many(
        "stock.location",
        compute="_compute_allowed_locations",
    )

    lot_id = fields.Many2one(
        "stock.lot",
        string="Lot",
    )

    expiration_date = fields.Date(
        string="Date expiration",
    )

    qty_system = fields.Float(
        string="Qté théorique",
        digits="Product Unit of Measure",
    )

    qty_counted = fields.Float(
        string="Qté comptée",
        digits="Product Unit of Measure",
    )

    difference = fields.Float(
        string="Écart",
        compute="_compute_difference",
        store=True,
        digits="Product Unit of Measure",
    )

    difference_percent = fields.Float(
        string="% Écart",
        compute="_compute_difference_percent",
        store=True,
    )

    is_difference = fields.Boolean(
        string="Écart détecté",
        compute="_compute_inventory_status",
        store=True,
    )

    difference_type = fields.Selection(
        [
            ("equal", "Conforme"),
            ("missing", "Manquant"),
            ("excess", "Surplus"),
        ],
        string="Statut",
        compute="_compute_inventory_status",
        store=True,
    )

    is_manual = fields.Boolean(
        string="Ajout manuel",
        default=False,
    )


    location_difference = fields.Boolean(
        string="Déplacement détecté",
        compute="_compute_location_difference",
        store=True,
    )

    note = fields.Char(
        string="Observation",
    )

    adjustment_applied = fields.Boolean(
        string="Ajustement appliqué",
        default=False,
        readonly=True,
    )

    quant_id = fields.Many2one(
        "stock.quant",
        string="Quant Odoo",
        readonly=True,
    )

    validated = fields.Boolean(
        string="Validé",
        default=False,
    )

    generated = fields.Boolean(
        string="Générée",
        default=False,
        readonly=True,
    )

    barcode_scan = fields.Char(
        string="Scanner produit"
    )

    barcode = fields.Char(
        related="product_id.barcode",
        string="Code-barres",
        store=True,
    )

    def action_open_product(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Produit",
            "res_model": "product.product",
            "res_id": self.product_id.id,
            "view_mode": "form",
            "target": "current",
        }

    
    @api.onchange("barcode_scan")
    def _onchange_barcode_scan(self):

        if not self.barcode_scan:
            return

        barcode = self.barcode_scan.strip()

        product = self.env["product.product"].search(
            [
                ("barcode", "=", barcode)
            ],
            limit=1
        )

        if not product:

            self.barcode_scan = False

            return {
                "warning": {
                    "title": "Produit introuvable",
                    "message": (
                        f"Aucun produit trouvé pour "
                        f"le code-barres {barcode}"
                    )
                }
            }

        existing_line = self.line_ids.filtered(
            lambda l:
                l.product_id.id == product.id
        )[:1]

        if not existing_line:

            self.line_ids += self.env[
                "primetech.inventory.count.line"
            ].new({

                "product_id": product.id,

                "count_location_id":
                    self.location_id.id,

                "is_manual": True,
            })

        self.barcode_scan = False

    @api.depends("qty_system", "qty_counted")
    def _compute_difference(self):

        for rec in self:
            rec.difference = (
                rec.qty_counted - rec.qty_system
            )

    @api.depends("qty_system", "qty_counted")
    def _compute_difference_percent(self):

        for rec in self:

            if not rec.qty_system:
                rec.difference_percent = 0.0
                continue

            rec.difference_percent = (
                (
                    rec.qty_counted
                    - rec.qty_system
                )
                / rec.qty_system
            ) * 100

    @api.depends(
        "qty_system",
        "qty_counted",
    )
    def _compute_inventory_status(self):

        for rec in self:

            qty_system = rec.qty_system or 0.0
            qty_counted = rec.qty_counted or 0.0

            if qty_counted == qty_system:

                rec.is_difference = False
                rec.difference_type = "equal"

            elif qty_counted > qty_system:

                rec.is_difference = True
                rec.difference_type = "excess"

            else:

                rec.is_difference = True
                rec.difference_type = "missing"

    @api.depends(
        "sheet_id.location_id",
        "sheet_id.warehouse_id"
    )
    def _compute_allowed_locations(self):

        Location = self.env["stock.location"]

        for rec in self:

            if rec.sheet_id.location_id:

                rec.allowed_location_ids = Location.search([
                    (
                        "id",
                        "child_of",
                        rec.sheet_id.location_id.id
                    )
                ])

            else:

                rec.allowed_location_ids = False

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            sheet = self.env[
                "primetech.inventory.count.sheet"
            ].browse(vals.get("sheet_id"))

            if not sheet.location_id:

                raise ValidationError(
                    "Veuillez sélectionner un emplacement avant d'ajouter une ligne."
                )

        return super().create(vals_list)
    
    @api.onchange("location_id")
    def _onchange_location_id(self):

        for line in self.line_ids:

            line.count_location_id = False

    @api.onchange("product_id")
    def _onchange_product_id(self):

        self.lot_id = False
        self.expiration_date = False

        if self.product_id:

            self.count_location_id = (
                self.sheet_id.location_id
            )

    @api.constrains("qty_counted")
    def _check_qty_counted(self):

        for rec in self:

            if rec.qty_counted < 0:

                raise ValidationError(
                    "La quantité comptée ne peut pas être négative."
                )


    def unlink(self):

        for rec in self:

            if rec.sheet_id.state in (
                "validated",
                "done",
            ):
                raise UserError(
                    "Impossible de supprimer une ligne d'un inventaire validé."
                )

        return super().unlink()

    @api.onchange("product_id")
    def _onchange_product_id(self):

        self.lot_id = False
        self.expiration_date = False

        if self.product_id:

            self.count_location_id = (
                self.sheet_id.location_id
            )

            return {
                "domain": {
                    "lot_id": [
                        (
                            "product_id",
                            "=",
                            self.product_id.id
                        )
                    ]
                }
            }
        
    @api.model_create_multi
    def create(self, vals_list):

        records = super().create(vals_list)

        for rec in records:

            if (
                rec.lot_id
                and rec.expiration_date
            ):

                rec.lot_id.write({
                    "expiration_date":
                        rec.expiration_date
                })

        return records
    
    def write(self, vals):

        res = super().write(vals)

        for rec in self:

            if (
                rec.lot_id
                and rec.expiration_date
            ):

                rec.lot_id.write({
                    "expiration_date":
                        rec.expiration_date
                })

        return res

