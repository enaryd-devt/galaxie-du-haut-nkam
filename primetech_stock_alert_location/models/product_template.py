# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    stock_alert_ids = fields.One2many(
        comodel_name="stock.location.alert",
        inverse_name="product_tmpl_id",
        string="Stock par emplacement",
        copy=False,
    )

    def action_sync_stock(self):

        quants = self.env["stock.quant"].search([
            ("product_id.product_tmpl_id", "in", self.ids),
            ("location_id.usage", "=", "internal"),
        ])

        quants.sync_stock_alerts()

        return True

    def _sync_stock_alerts(self):

        Alert = self.env["stock.location.alert"]
        Quant = self.env["stock.quant"]

        for product in self:

            quants = Quant.search([
                ("product_id.product_tmpl_id", "=", product.id),
                ("location_id.usage", "=", "internal"),
                ("quantity", ">", 0),
            ])

            old_lines = Alert.search([
                ("product_tmpl_id", "=", product.id),
            ])

            # On conserve les seuils d'alerte
            minimums = {
                (
                    l.product_id.id,
                    l.location_id.id,
                    l.lot_id.id if l.lot_id else False,
                ): l.minimum_qty
                for l in old_lines
            }

            old_lines.unlink()

            for quant in quants:

                key = (
                    quant.product_id.id,
                    quant.location_id.id,
                    quant.lot_id.id if quant.lot_id else False,
                )

                Alert.create({
                    "product_tmpl_id": product.id,
                    "product_id": quant.product_id.id,
                    "location_id": quant.location_id.id,
                    "lot_id": quant.lot_id.id or False,
                    "quantity": quant.quantity,
                    "reserved_quantity": quant.reserved_quantity,
                    "minimum_qty": minimums.get(key, 0),
                })
    
    def read(self, fields=None, load="_classic_read"):

        self._sync_stock_alerts()

        return super().read(fields=fields, load=load)
    
    stock_alert_ids = fields.One2many(
        "stock.location.alert",
        "product_tmpl_id",
        string="Stock par emplacement",
    )

    has_stock_alerts = fields.Boolean(
        string="Has Stock Alerts",
        compute="_compute_has_stock_alerts",
    )

    @api.depends("product_variant_ids.stock_quant_ids")
    def _compute_has_stock_alerts(self):

        Quant = self.env["stock.quant"]

        for product in self:

            product.has_stock_alerts = bool(

                Quant.search_count([

                    ("product_id.product_tmpl_id", "=", product.id),
                    ("location_id.usage", "=", "internal"),
                    ("quantity", ">", 0),

                ])

            )