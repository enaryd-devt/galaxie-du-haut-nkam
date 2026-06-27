# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    packaging_summary = fields.Html(
        related="product_tmpl_id.packaging_summary",
        readonly=True,
    )

    warehouse_summary = fields.Html(
        related="product_tmpl_id.warehouse_summary",
        readonly=True,
    )

    location_summary = fields.Html(
        related="product_tmpl_id.location_summary",
        readonly=True,
    )

    has_stock_alerts = fields.Boolean(
        related="product_tmpl_id.has_stock_alerts",
        readonly=True,
    )

    stock_alert_ids = fields.One2many(
        related="product_tmpl_id.stock_alert_ids",
        readonly=True,
    )

    def action_sync_stock(self):
        """Utilise la logique du template."""
        return self.product_tmpl_id.action_sync_stock()