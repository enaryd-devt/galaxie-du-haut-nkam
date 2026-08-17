# -*- coding: utf-8 -*-

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()

        vals = super()._prepare_invoice_line(**optional_values)

        # Le conditionnement choisi est transmis à la ligne de facture.
        # L'entrepôt est lu directement depuis les sale_line_ids liées par
        # account.move.line, y compris quand plusieurs commandes sont liées.
        vals.update({
            "product_packaging_id": self.product_packaging_id.id if self.product_packaging_id else False,
        })

        return vals
