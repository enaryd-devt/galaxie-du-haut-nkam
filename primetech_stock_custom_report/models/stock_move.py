from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    # ==========================================================
    # AFFICHAGE CONDITIONNEMENT
    # ==========================================================

    packaging_qty = fields.Float(
        string="Qté conditionnement",
        compute="_compute_packaging_display",
    )

    packaging_name = fields.Char(
        string="Conditionnement",
        compute="_compute_packaging_display",
    )

    has_remaining = fields.Boolean(
        compute="_compute_packaging_display",
    )

    remaining_qty = fields.Float(
        compute="_compute_packaging_display",
    )

    remaining_name = fields.Char(
        compute="_compute_packaging_display",
    )

    ordered_packaging_qty = fields.Float(
        compute="_compute_packaging_display",
    )

    ordered_packaging_name = fields.Char(
        compute="_compute_packaging_display",
    )

    ordered_remaining_qty = fields.Float(
        compute="_compute_packaging_display",
    )

    ordered_remaining_name = fields.Char(
        compute="_compute_packaging_display",
    )

    ordered_has_remaining = fields.Boolean(
        compute="_compute_packaging_display",
    )

    done_packaging_qty = fields.Float(
        compute="_compute_packaging_display",
    )

    done_packaging_name = fields.Char(
        compute="_compute_packaging_display",
    )

    done_remaining_qty = fields.Float(
        compute="_compute_packaging_display",
    )

    done_remaining_name = fields.Char(
        compute="_compute_packaging_display",
    )

    done_has_remaining = fields.Boolean(
        compute="_compute_packaging_display",
    )

    @api.depends(
        "product_uom_qty",
        "move_line_ids.quantity",
        "product_packaging_id",
        "product_uom",
        "state",
    )
    def _compute_packaging_display(self):

        for move in self:

            # =====================================================
            # INITIALISATION (OBLIGATOIRE)
            # =====================================================

            move.packaging_qty = 0.0
            move.packaging_name = ""
            move.remaining_qty = 0.0
            move.remaining_name = ""
            move.has_remaining = False

            move.ordered_packaging_qty = 0.0
            move.ordered_packaging_name = ""
            move.ordered_remaining_qty = 0.0
            move.ordered_remaining_name = ""
            move.ordered_has_remaining = False

            move.done_packaging_qty = 0.0
            move.done_packaging_name = ""
            move.done_remaining_qty = 0.0
            move.done_remaining_name = ""
            move.done_has_remaining = False

            # =====================================================
            # QUANTITE COMMANDEE
            # =====================================================

            ordered = move._get_packaging_values(
                move.product_uom_qty,
                move.product_packaging_id,
                move.product_uom,
            )

            move.ordered_packaging_qty = ordered["packaging_qty"]
            move.ordered_packaging_name = ordered["packaging_name"]
            move.ordered_remaining_qty = ordered["remaining_qty"]
            move.ordered_remaining_name = ordered["remaining_name"]
            move.ordered_has_remaining = ordered["has_remaining"]

            # =====================================================
            # COMPATIBILITE AVEC LE QWEB
            # =====================================================

            move.packaging_qty = ordered["packaging_qty"]
            move.packaging_name = ordered["packaging_name"]
            move.remaining_qty = ordered["remaining_qty"]
            move.remaining_name = ordered["remaining_name"]
            move.has_remaining = ordered["has_remaining"]

            # =====================================================
            # QUANTITE LIVREE
            # =====================================================

            if move.state == "done":

                qty_done = sum(
                    ml.quantity if hasattr(ml, "quantity") else ml.qty_done
                    for ml in move.move_line_ids
                )

            else:

                # =====================================================
                # QUANTITE LIVREE
                # =====================================================

                qty_done = 0.0

                if move.state == "done":
                    qty_done = sum(move.move_line_ids.mapped("quantity"))

                delivered = move._get_packaging_values(
                    qty_done,
                    move.product_packaging_id,
                    move.product_uom,
                )

                move.done_packaging_qty = delivered["packaging_qty"]
                move.done_packaging_name = delivered["packaging_name"]
                move.done_remaining_qty = delivered["remaining_qty"]
                move.done_remaining_name = delivered["remaining_name"]
                move.done_has_remaining = delivered["has_remaining"]

    def _get_packaging_values(self, quantity, packaging, uom):

        result = {
            "packaging_qty": quantity,
            "packaging_name": uom.display_name if uom else "",
            "remaining_qty": 0.0,
            "remaining_name": "",
            "has_remaining": False,
        }

        if not packaging:
            return result

        if packaging.qty <= 0:
            return result

        full = int(quantity // packaging.qty)

        remain = quantity % packaging.qty

        if full == 0:
            return result

        result["packaging_qty"] = full
        result["packaging_name"] = packaging.name

        if remain:

            result["has_remaining"] = True
            result["remaining_qty"] = remain
            result["remaining_name"] = uom.display_name

        return result