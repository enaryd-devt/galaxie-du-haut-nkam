# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PrimetechReplenishmentLine(models.Model):
    _name = 'primetech.replenishment.line'
    _description = "Ligne de demande de réapprovisionnement"

    request_id = fields.Many2one(
        'primetech.replenishment.request', string="Demande",
        required=True, ondelete='cascade')

    state = fields.Selection(related='request_id.state', store=True)

    product_id = fields.Many2one(
        'product.product', string="Produit", required=True,
        domain=[('type', 'in', ('product', 'consu'))])

    uom_id = fields.Many2one(
        'uom.uom', string="Unité de mesure")

    requested_qty = fields.Float(
        string="Quantité demandée", required=True, default=1.0)

    approved_qty = fields.Float(string="Quantité approuvée")

    shop_stock_qty = fields.Float(
        string="Stock actuel en boutique", compute='_compute_shop_stock_qty')

    warehouse_stock_qty = fields.Float(
        string="Stock disponible au magasin", compute='_compute_warehouse_stock_qty')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.uom_id = line.product_id.uom_id

    def _compute_shop_stock_qty(self):
        for line in self:
            location = line.request_id.shop_id.location_id
            if location and line.product_id:
                line.shop_stock_qty = line.product_id.with_context(
                    location=location.id).qty_available
            else:
                line.shop_stock_qty = 0.0

    def _compute_warehouse_stock_qty(self):
        for line in self:
            warehouse = line.request_id.warehouse_id
            if warehouse and line.product_id:
                line.warehouse_stock_qty = line.product_id.with_context(
                    location=warehouse.lot_stock_id.id).qty_available
            else:
                line.warehouse_stock_qty = 0.0
