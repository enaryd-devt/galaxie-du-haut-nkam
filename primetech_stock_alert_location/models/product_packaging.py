# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from markupsafe import Markup


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    

    uom_name = fields.Char(
        string="Unité",
        compute="_compute_packaging_stock",
    )
    
    purchase_ok = fields.Boolean(
        string="Achat",
        default=True,
    )

    sale_ok = fields.Boolean(
        string="Vente",
        default=True,
    )
    
    # ============================================================
    # CODE BARRE DU CONDITIONNEMENT
    # ============================================================

    barcode = fields.Char(
        string="Code-barres",
        copy=False,
        index=True,
    )

    # ============================================================
    # STOCK
    # ============================================================

    stock_available = fields.Float(
        string="Stock actuel",
        compute="_compute_packaging_stock",
        digits="Product Unit of Measure",
        store=False,
    )

    packaging_count = fields.Integer(
        string="Nb conditionnements",
        compute="_compute_packaging_stock",
        store=False,
    )

    remaining_qty = fields.Float(
        string="Reste",
        compute="_compute_packaging_stock",
        digits="Product Unit of Measure",
        store=False,
    )

    equivalent_display = fields.Html(
        string="Répartition du stock",
        compute="_compute_packaging_stock",
        sanitize=False,
    )


    # ============================================================
    # COULEUR
    # ============================================================

    display_color = fields.Selection(
        [
            ("success", "Vert"),
            ("warning", "Orange"),
            ("danger", "Rouge"),
        ],
        compute="_compute_packaging_stock",
        store=False,
    )

    ##############################################################
    # CONVERSION
    ##############################################################

    scan_quantity = fields.Float(
        string="Qté scannée",
        default=1.0,
    )

    unit_quantity = fields.Float(
        string="Quantité totale",
        compute="_compute_conversion",
        digits="Product Unit of Measure",
    )

    display_conversion = fields.Char(
        string="Conversion",
        compute="_compute_conversion",
    )


    ##############################################################
    # CONVERSION
    ##############################################################

    @api.depends(
        "scan_quantity",
        "qty",
    )
    def _compute_conversion(self):

        for rec in self:

            rec.unit_quantity = rec.scan_quantity * rec.qty

            if rec.scan_quantity <= 1:

                rec.display_conversion = (
                    "%s %s = %s unité(s)"
                    % (
                        int(rec.scan_quantity),
                        rec.name,
                        int(rec.unit_quantity),
                    )
                )

            else:

                rec.display_conversion = (
                    "%s %s = %s unité(s)"
                    % (
                        int(rec.scan_quantity),
                        rec.name,
                        int(rec.unit_quantity),
                    )
                )

    # ============================================================
    # CALCULS
    # ============================================================


    from markupsafe import Markup

    @api.depends(
        "qty",
        "product_id.qty_available",
        "product_id.uom_id",
    )
    def _compute_packaging_stock(self):

        for rec in self:

            rec.stock_available = 0.0
            rec.packaging_count = 0
            rec.remaining_qty = 0.0
            rec.equivalent_display = ""
            rec.display_color = "danger"

            if not rec.product_id:
                continue

            stock = rec.product_id.qty_available

            rec.stock_available = stock

            uom = rec.product_id.uom_id.display_name or "Unité"

            if rec.qty <= 0:

                rec.remaining_qty = stock

                rec.equivalent_display = Markup("""
                    <div class="pt-packaging-empty">
                        <i class="fa fa-circle-info"></i>
                        Conditionnement non défini
                    </div>
                """)

                continue

            full = int(stock // rec.qty)

            remain = stock % rec.qty

            rec.packaging_count = full

            rec.remaining_qty = remain

            packaging_label = rec.name

            unit_label = uom

            # ==========================================
            # RUPTURE
            # ==========================================

            if stock <= 0:

                rec.display_color = "danger"

                rec.equivalent_display = Markup("""
                    <div class="pt-packaging-danger">

                        <i class="fa fa-circle-xmark"></i>

                        <span>Rupture de stock</span>

                    </div>
                """)

                continue

            # ==========================================
            # CONDITIONNEMENTS COMPLETS
            # ==========================================

            if remain == 0:

                rec.display_color = "success"

                rec.equivalent_display = Markup(f"""
                    <div class="pt-packaging-success">

                        <i class="fa fa-box-open"></i>

                        <strong>{full}</strong>

                        <span>{packaging_label}</span>

                    </div>
                """)

                continue

            # ==========================================
            # STOCK MIXTE
            # ==========================================

            rec.display_color = "warning"

            rec.equivalent_display = Markup(f"""
                <div class="pt-packaging">

                    <div class="pt-main">

                        <i class="fa fa-box-open"></i>

                        <strong>{full}</strong>

                        <span>{packaging_label}</span>

                    </div>

                    <div class="pt-sub">

                        <i class="fa fa-cube"></i>

                        <span>{int(remain)} {unit_label}</span>

                    </div>

                </div>
            """)
   
    @api.constrains("qty")
    def _check_packaging_qty(self):

        for rec in self:

            if rec.qty <= 0:
                raise ValidationError(
                    "La quantité du conditionnement doit être supérieure à zéro."
                )
            
    ##############################################################
    # OUTILS
    ##############################################################

    def convert_to_units(self, quantity=1):

        self.ensure_one()

        return quantity * self.qty


    def convert_from_units(self, quantity):

        self.ensure_one()

        if not self.qty:

            return (0, quantity)

        full = int(quantity // self.qty)

        remain = quantity % self.qty

        return (full, remain)
    
    
    # ============================================================
    # NOM AUTOMATIQUE
    # ============================================================

    @api.onchange("qty")
    def _onchange_qty(self):

        for rec in self:

            if not rec.name and rec.qty:

                rec.name = "Conditionnement %s" % int(rec.qty)
    # ============================================================
    # INFORMATIONS
    # ============================================================

    def get_available_stock(self):

        self.ensure_one()

        return self.product_id.qty_available

    def get_packaging_stock(self):

        self.ensure_one()

        if not self.qty:

            return 0

        return int(self.product_id.qty_available // self.qty)

    def get_remaining_stock(self):

        self.ensure_one()

        if not self.qty:

            return self.product_id.qty_available

        return self.product_id.qty_available % self.qty