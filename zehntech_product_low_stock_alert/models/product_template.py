from odoo import models, fields, api
from datetime import datetime, date
import json
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # =====================================================
    # DISCOUNT
    # =====================================================

    discount_percent = fields.Float(
        string="Remise (%)",
        compute="_compute_discount_percent",
        inverse="_inverse_discount_percent",
        store=False,
    )
    
    # =====================================================
    # STOCK ALERT
    # =====================================================

    alert_quantity = fields.Float(
        string="Alerte",
        compute="_compute_alert_quantity",
        inverse="_inverse_alert_quantity",
        store=False
    )

    qty_available = fields.Float(
        string="Quantity On Hand",
        store=False
    )

    # =====================================================
    # OPTIMAL STOCK
    # =====================================================

    optimal_quantity = fields.Float(
        string="Optimale+",
        compute="_compute_optimal_quantity",
        inverse="_inverse_optimal_quantity",
        store=False
    )


    # =====================================================
    # COLOR LOW STOCK
    # =====================================================

    color_field = fields.Char(
        string="Color",
        compute='_compute_color_field',
        store=False
    )


    # =====================================================
    # LOT EXPIRATION ALERT (KANBAN)
    # =====================================================

    lot_alert_ids = fields.Text(
        string="Lot Alerts",
        compute="_compute_lot_alert_ids",
        store=False
    )

    # =====================================================
    # MARGIN (KANBAN)
    # =====================================================

    margin_amount = fields.Float(
        string="Margin",
        compute="_compute_margin_amount",
        store=False
    )
    @api.depends('list_price', 'standard_price')
    def _compute_margin_amount(self):
        for product in self:
            product.margin_amount = product.list_price - product.standard_price


    # =====================================================
    # REMISE LIST
    # =====================================================

    @api.depends("product_variant_ids.discount_percent")
    def _compute_discount_percent(self):

        for template in self:

            template.discount_percent = (
                template.product_variant_ids[0].discount_percent
                if template.product_variant_ids
                else 0.0
            )


    def _inverse_discount_percent(self):

        for template in self:

            if template.product_variant_ids:

                template.product_variant_ids.write({
                    "discount_percent": template.discount_percent
                })
    
    discount_display = fields.Char(
        string="Remise",
        compute="_compute_discount_display",
    )
        
    @api.depends("discount_percent")
    def _compute_discount_display(self):

        for rec in self:

            if rec.discount_percent > 0:

                rec.discount_display = (
                    f"{int(rec.discount_percent)}%"
                    if rec.discount_percent.is_integer()
                    else f"{rec.discount_percent}%"
                )

            else:

                rec.discount_display = ""
    






  

    # =====================================================
    # COLOR COMPUTE
    # =====================================================

    @api.depends('qty_available', 'alert_quantity')
    def _compute_color_field(self):
        for product in self:
            product.color_field = (
                '#f08080' if product.qty_available <= product.alert_quantity else ''
            )

    # =====================================================
    # ALERT QUANTITY
    # =====================================================

    @api.depends('product_variant_ids.alert_quantity')
    def _compute_alert_quantity(self):
        for template in self:
            template.alert_quantity = (
                template.product_variant_ids[0].alert_quantity
                if template.product_variant_ids
                else 0.0
            )

    def _inverse_alert_quantity(self):
        for template in self:
            if template.product_variant_ids:
                template.product_variant_ids[0].alert_quantity = template.alert_quantity

    # =====================================================
    # OPTIMAL QUANTITY
    # =====================================================

    @api.depends('product_variant_ids.optimal_quantity')
    def _compute_optimal_quantity(self):
        for template in self:
            template.optimal_quantity = (
                template.product_variant_ids[0].optimal_quantity
                if template.product_variant_ids
                else 0.0
            )

    def _inverse_optimal_quantity(self):
        for template in self:
            if template.product_variant_ids:
                template.product_variant_ids.write({
                    'optimal_quantity': template.optimal_quantity
                })

    # =====================================================
    # LOT EXPIRATION ALERT (AMÉLIORÉ)
    # =====================================================

    def _compute_lot_alert_ids(self):

        today = fields.Date.context_today(self)
        if isinstance(today, datetime):
            today = today.date()

        warning_days = 7  # seuil avant expiration

        for template in self:

            alerts = []

            # uniquement produits suivis par lot
            if template.tracking != 'lot':
                template.lot_alert_ids = json.dumps([])
                continue

            lots = self.env['stock.lot'].search([
                ('product_id', 'in', template.product_variant_ids.ids),
                ('expiration_date', '!=', False),
                ('product_qty', '>', 0),
            ])

            for lot in lots:

                expiration_date = lot.expiration_date

                # normalisation date
                if isinstance(expiration_date, str):
                    expiration_date = fields.Date.from_string(expiration_date)
                elif isinstance(expiration_date, datetime):
                    expiration_date = expiration_date.date()

                if not expiration_date:
                    continue

                # =====================================================
                # LOGIQUE EXPIRATION
                # =====================================================

                days_left = (expiration_date - today).days

                if days_left < 0:
                    status = "expired"
                elif days_left <= warning_days:
                    status = "warning"
                else:
                    status = "ok"

                # =====================================================
                # OUTPUT JSON
                # =====================================================

                alerts.append({
                    'name': lot.name or '',
                    'expiration_date': expiration_date.strftime('%Y-%m-%d'),
                    'expiration_date_display': expiration_date.strftime('%d/%m/%Y'),
                    'product_qty': round(lot.product_qty, 2),
                    'days_left': days_left,
                    'status': status,
                    'is_expired': status == "expired",
                })

            template.lot_alert_ids = json.dumps(alerts)