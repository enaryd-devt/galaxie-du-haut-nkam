# -*- coding: utf-8 -*-

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):

        self.ensure_one()

        vals = super()._prepare_invoice_line(**optional_values)

        vals.update({

            "product_packaging_id":
                self.product_packaging_id.id if self.product_packaging_id else False,

            "packaging_qty":
                self.product_uom_qty,

            "packaging_price":
                self.price_unit,

        })

        return vals