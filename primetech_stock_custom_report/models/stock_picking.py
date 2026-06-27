# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    packaging_qty = fields.Float(
        string="Nb Cond.",
        default=0.0,
        copy=False,
    )

    @api.onchange("product_packaging_id")
    def _onchange_product_packaging(self):
        """Synchronise le nombre de conditionnements lorsqu'un
        conditionnement est sélectionné.
        """
        for move in self:

            if not move.product_packaging_id:
                move.packaging_qty = 0.0
                continue

            if move.product_packaging_id.qty <= 0:
                move.packaging_qty = 0.0
                continue

            if move.product_uom_qty:

                move.packaging_qty = (
                    move.product_uom_qty
                    / move.product_packaging_id.qty
                )

            else:

                move.packaging_qty = 1.0
                move.product_uom_qty = move.product_packaging_id.qty

    @api.onchange("product_uom_qty")
    def _onchange_product_uom_qty(self):
        """Si l'utilisateur modifie la quantité,
        le nombre de conditionnements est recalculé.
        """

        for move in self:

            if not move.product_packaging_id:
                move.packaging_qty = 0.0
                continue

            if move.product_packaging_id.qty <= 0:
                move.packaging_qty = 0.0
                continue

            move.packaging_qty = (
                move.product_uom_qty
                / move.product_packaging_id.qty
            )

    @api.onchange("packaging_qty")
    def _onchange_packaging_qty(self):
        """Si l'utilisateur modifie le nombre de conditionnements,
        la quantité est recalculée.
        """

        for move in self:

            if not move.product_packaging_id:
                continue

            if move.product_packaging_id.qty <= 0:
                continue

            move.product_uom_qty = (
                move.packaging_qty
                * move.product_packaging_id.qty
            )