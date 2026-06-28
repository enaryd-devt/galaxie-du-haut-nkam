from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_packaging_id = fields.Many2one(
        "product.packaging",
        string="Conditionnement",
        readonly=True,
        copy=False,
    )

    packaging_qty = fields.Float(
        string="Qté conditionnement",
        readonly=True,
        copy=False,
    )

    packaging_price = fields.Float(
        string="Prix conditionnement",
        digits="Product Price",
        readonly=True,
        copy=False,
    )

    packaging_qty = fields.Integer(
        string="Nb conditionnements",
        compute="_compute_packaging_display",
    )

    packaging_name = fields.Char(
        string="Conditionnement",
        compute="_compute_packaging_display",
    )

    packaging_unit_price = fields.Monetary(
        string="Prix conditionnement",
        currency_field="currency_id",
        compute="_compute_packaging_display",
    )

    packaging_subtotal = fields.Monetary(
        string="Sous-total conditionnement",
        currency_field="currency_id",
        compute="_compute_packaging_display",
    )

    remaining_qty = fields.Float(
        string="Qté restante",
        compute="_compute_packaging_display",
    )

    remaining_name = fields.Char(
        string="Libellé reste",
        compute="_compute_packaging_display",
    )

    remaining_unit_price = fields.Monetary(
        string="Prix unité",
        currency_field="currency_id",
        compute="_compute_packaging_display",
    )

    remaining_subtotal = fields.Monetary(
        string="Sous-total reste",
        currency_field="currency_id",
        compute="_compute_packaging_display",
    )

    has_remaining = fields.Boolean(
        compute="_compute_packaging_display",
    )

    display_packaging_qty = fields.Char(
        compute="_compute_packaging_display",
    )

    

    def _prepare_invoice_line(self, **optional_values):
        vals = super()._prepare_invoice_line(**optional_values)

        vals.update({
            "product_packaging_id": self.product_packaging_id.id or False,
            "packaging_qty": self.product_packaging_qty,
            "packaging_price": self.price_unit,
        })

        return vals
    
    @api.depends(
        "quantity",
        "price_unit",
        "price_subtotal",
        "product_packaging_id",
        "product_uom_id",
    )
    def _compute_packaging_display(self):

        for line in self:

            # Initialisation
            line.packaging_qty = 0
            line.packaging_name = ""
            line.packaging_unit_price = 0
            line.packaging_subtotal = 0

            line.remaining_qty = 0
            line.remaining_name = ""
            line.remaining_unit_price = 0
            line.remaining_subtotal = 0

            line.has_remaining = False
            line.display_packaging_qty = ""

            # Pas de conditionnement
            if not line.product_packaging_id:

                line.packaging_qty = line.quantity

                line.packaging_name = line.product_uom_id.display_name

                line.display_packaging_qty = (
                    f"{int(line.quantity):02d} × {line.product_uom_id.display_name}"
                )

                line.packaging_unit_price = line.price_unit

                line.packaging_subtotal = line.price_subtotal

                line.has_remaining = False

                continue

            packaging = line.product_packaging_id

            if packaging.qty <= 0:

                line.packaging_qty = line.quantity

                line.packaging_name = line.product_uom_id.display_name

                line.display_packaging_qty = (
                    f"{int(line.quantity):02d} × {line.product_uom_id.display_name}"
                )

                line.packaging_unit_price = line.price_unit

                line.packaging_subtotal = line.price_subtotal

                line.has_remaining = False

                continue

            ###############################################
            # Décomposition
            ###############################################

            full = int(line.quantity // packaging.qty)
            remain = line.quantity % packaging.qty

            ###############################################
            # Conditionnement
            ###############################################

            line.packaging_qty = full
            line.packaging_name = packaging.name

            line.display_packaging_qty = (
                f"{full:02d} × {packaging.name}"
            )

            # Prix d'un conditionnement
            line.packaging_unit_price = (
                line.price_unit * packaging.qty
            )

            # Sous-total des conditionnements
            line.packaging_subtotal = (
                full * line.packaging_unit_price
            )

            ###############################################
            # Reste
            ###############################################

            if remain:

                line.has_remaining = True

                line.remaining_qty = remain

                line.remaining_name = (
                    line.product_uom_id.display_name
                )

                # Prix UoM inchangé
                line.remaining_unit_price = line.price_unit

                line.remaining_subtotal = (
                    remain * line.price_unit
                )


