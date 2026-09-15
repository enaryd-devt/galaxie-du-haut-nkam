# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Conditionnement d'origine (repris de la ligne de commande via
    # sale_order_line._prepare_invoice_line).
    product_packaging_id = fields.Many2one(
        "product.packaging",
        string="Conditionnement",
        readonly=True,
        copy=False,
    )

    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Magasin",
        compute="_compute_sale_line_warehouses",
        readonly=True,
        copy=False,
        help="Entrepôt de la ligne de commande client à l'origine de cette ligne.",
    )

    warehouse_names = fields.Char(
        string="Magasins des lignes de commande",
        compute="_compute_sale_line_warehouses",
        help="Noms des entrepôts définis sur les lignes de commande liées.",
    )

    @api.depends("sale_line_ids.warehouse_id")
    def _compute_sale_line_warehouses(self):
        for line in self:
            # Une ligne de facture peut regrouper des lignes provenant de
            # plusieurs bons de commande : toutes doivent être prises en
            # compte, sans utiliser warehouse_id de l'en-tête de commande.
            warehouses = line.sale_line_ids.mapped("warehouse_id")
            line.warehouse_id = warehouses[:1]
            line.warehouse_names = ", ".join(warehouses.mapped("display_name"))

    # -- Champs calcules utilises pour l'affichage sur la facture --
    # Logique "conditionnement strict" : on affiche la quantite en
    # conditionnement UNIQUEMENT si la quantite vendue est un multiple
    # exact du conditionnement (ex: 50 -> "5 Carton de 10"). Sinon on
    # affiche normalement en unite de vente (ex: 53 -> "53 Unites").
    # Ainsi, une ligne de facture = une seule ligne affichee, jamais de
    # ligne de reliquat.

    packaging_qty = fields.Float(
        string="Qte affichee",
        compute="_compute_packaging_display",
        help="Nombre de conditionnements si la quantite est un multiple "
             "exact du conditionnement, sinon quantite en unite de vente.",
    )

    packaging_name = fields.Char(
        string="Conditionnement / Unite",
        compute="_compute_packaging_display",
    )

    packaging_unit_price = fields.Monetary(
        string="Prix unitaire affiche",
        currency_field="currency_id",
        compute="_compute_packaging_display",
        help="Prix du conditionnement si affiche en conditionnement, "
             "sinon prix unitaire normal.",
    )

    @api.depends(
        "quantity",
        "price_unit",
        "product_packaging_id",
        "product_uom_id",
    )
    def _compute_packaging_display(self):
        for line in self:
            packaging = line.product_packaging_id
            precision = line.product_uom_id.rounding or 0.01

            use_packaging = False
            if packaging and packaging.qty > 0:
                remainder = line.quantity % packaging.qty
                use_packaging = float_is_zero(remainder, precision_rounding=precision)

            if use_packaging:
                line.packaging_qty = line.quantity / packaging.qty
                line.packaging_name = packaging.name
                line.packaging_unit_price = line.price_unit * packaging.qty
            else:
                line.packaging_qty = line.quantity
                line.packaging_name = line.product_uom_id.display_name
                line.packaging_unit_price = line.price_unit
