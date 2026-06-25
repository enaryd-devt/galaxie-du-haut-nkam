# -*- coding: utf-8 -*-

from odoo import fields, models


class AssociationIncome(models.Model):
    _name = "association.income"
    _description = "Association Income"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "income_date desc, id desc"

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )

    name = fields.Char(required=True)

    income_date = fields.Date(
        default=fields.Date.context_today,
    )

    amount = fields.Monetary(
        currency_field="currency_id",
    )

    source = fields.Char()

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("received", "Received"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
    )

    note = fields.Html()