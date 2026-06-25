# -*- coding: utf-8 -*-

from odoo import models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def sync_stock_alerts(self):

        Alert = self.env["stock.location.alert"]

        templates = self.mapped("product_id.product_tmpl_id")

        for template in templates:

            quants = self.search([
                ("product_id.product_tmpl_id", "=", template.id),
                ("location_id.usage", "=", "internal"),
            ])

            existing = Alert.search([
                ("product_tmpl_id", "=", template.id),
            ])

            # dictionnaire des lignes existantes
            existing_map = {}

            for line in existing:

                key = (
                    line.product_id.id,
                    line.location_id.id,
                    line.lot_id.id if line.lot_id else False,
                )

                existing_map[key] = line

            current_keys = []

            for quant in quants:

                key = (
                    quant.product_id.id,
                    quant.location_id.id,
                    quant.lot_id.id if quant.lot_id else False,
                )

                current_keys.append(key)

                values = {
                    "product_tmpl_id": template.id,
                    "product_id": quant.product_id.id,
                    "location_id": quant.location_id.id,
                    "lot_id": quant.lot_id.id or False,
                    "quantity": quant.quantity,
                    "reserved_quantity": quant.reserved_quantity,
                }

                if key in existing_map:

                    existing_map[key].write(values)

                else:

                    Alert.create(values)

            # suppression des anciennes lignes

            for key, line in existing_map.items():

                if key not in current_keys:

                    line.unlink()