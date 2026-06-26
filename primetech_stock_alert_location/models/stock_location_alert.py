# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockLocationAlert(models.Model):
    _name = "stock.location.alert"
    _description = "Stock Alert by Location"
    _order = "location_id, lot_id"

    # =====================================================
    # Relations
    # =====================================================

    product_tmpl_id = fields.Many2one(
        "product.template",
        required=True,
        ondelete="cascade",
    )

    product_id = fields.Many2one(
        "product.product",
        required=True,
        ondelete="cascade",
    )

    location_id = fields.Many2one(
        "stock.location",
        string="Emplacement",
        required=True,
    )

    lot_id = fields.Many2one(
        "stock.lot",
        string="Lot",
    )

    # =====================================================
    # Date de péremption
    # =====================================================

    expiration_date = fields.Date(
        string="Date de péremption",
        compute="_compute_expiration_date",
    )

    @api.depends("lot_id")
    def _compute_expiration_date(self):
        for rec in self:
            rec.expiration_date = (
                rec.lot_id.expiration_date
                if rec.lot_id
                else False
            )

    # =====================================================
    # Quantités
    # =====================================================

    quantity = fields.Float(
        string="Stock",
    )

    reserved_quantity = fields.Float(
        string="Réservé",
    )

    available_quantity = fields.Float(
        string="Disponible",
        compute="_compute_available_quantity",
    )

    minimum_qty = fields.Float(
        string="Seuil d'alerte",
        default=0.0,
    )

    # =====================================================
    # Etat
    # =====================================================

    status = fields.Selection(
        [
            ("ok", "Stock OK"),
            ("warning", "Stock faible"),
            ("alert", "Rupture"),
        ],
        string="Etat",
        compute="_compute_status",
    )

    status_html = fields.Html(
        compute="_compute_status_html",
        sanitize=False,
    )

    @api.depends("available_quantity", "minimum_qty")
    def _compute_status_html(self):

        for rec in self:

            if rec.available_quantity <= 0:

                rec.status_html = """
                <span style="
                    background:#FDECEC;
                    color:#C62828;
                    padding:3px 10px;
                    border-radius:20px;
                    font-weight:600;
                    font-size:12px;">
                    ⛔ Rupture
                </span>
                """

            elif rec.minimum_qty > 0 and rec.available_quantity <= rec.minimum_qty:

                rec.status_html = """
                <span style="
                    background:#FFF8E1;
                    color:#EF6C00;
                    padding:3px 10px;
                    border-radius:20px;
                    font-weight:600;
                    font-size:12px;">
                    ⚠ Stock faible
                </span>
                """

            else:

                rec.status_html = """
                <span style="
                    background:#E8F5E9;
                    color:#2E7D32;
                    padding:3px 10px;
                    border-radius:20px;
                    font-weight:600;
                    font-size:12px;">
                    ✓ Disponible
                </span>
                """

    # =====================================================
    # Disponible
    # =====================================================

    @api.depends("quantity", "reserved_quantity")
    def _compute_available_quantity(self):
        for rec in self:
            rec.available_quantity = (
                rec.quantity - rec.reserved_quantity
            )

    # =====================================================
    # Statut
    # =====================================================

    @api.depends("available_quantity", "minimum_qty")
    def _compute_status(self):
        for rec in self:

            if rec.available_quantity <= 0:
                rec.status = "alert"

            elif (
                rec.minimum_qty > 0
                and rec.available_quantity <= rec.minimum_qty
            ):
                rec.status = "warning"

            else:
                rec.status = "ok"