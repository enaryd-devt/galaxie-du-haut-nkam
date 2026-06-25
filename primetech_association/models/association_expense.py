# -*- coding: utf-8 -*-

from odoo import fields, models


class AssociationExpense(models.Model):
    _name = "association.expense"
    _description = "Association Expense"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "expense_date desc, id desc"

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

    name = fields.Char(
        required=True,
        tracking=True,
    )

    expense_date = fields.Date(
        default=fields.Date.context_today,
    )

    amount = fields.Monetary(
        currency_field="currency_id",
    )

    beneficiary = fields.Char()

    payment_method = fields.Selection(
        [
            ("cash", "Cash"),
            ("bank", "Bank"),
            ("mobile_money", "Mobile Money"),
            ("cheque", "Cheque"),
        ],
        default="cash",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("validated", "Validated"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
    )

    note = fields.Html()