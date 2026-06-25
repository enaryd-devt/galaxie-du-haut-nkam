# -*- coding: utf-8 -*-

from odoo import fields, models


class AssociationDonation(models.Model):
    _name = "association.donation"
    _description = "Association Donation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "donation_date desc, id desc"

    active = fields.Boolean(default=True, tracking=True)
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
        string="Reference",
        required=True,
        tracking=True,
    )

    donor = fields.Char(
        string="Donor",
    )

    member_id = fields.Many2one(
        "association.member",
        string="Member",
    )

    donation_date = fields.Date(
        default=fields.Date.context_today,
    )

    amount = fields.Monetary(
        currency_field="currency_id",
    )

    donation_type = fields.Selection(
        [
            ("cash", "Cash"),
            ("material", "Material"),
            ("service", "Service"),
        ],
        default="cash",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("received", "Received"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )

    note = fields.Html()