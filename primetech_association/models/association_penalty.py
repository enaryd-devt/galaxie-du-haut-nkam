# -*- coding: utf-8 -*-

from odoo import fields, models


class AssociationPenalty(models.Model):
    _name = "association.penalty"
    _description = "Association Penalty"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    active = fields.Boolean(default=True)

    name = fields.Char(
        required=True,
    )

    member_id = fields.Many2one(
        "association.member",
        required=True,
    )

    penalty_date = fields.Date(
        default=fields.Date.context_today,
    )

    penalty_type = fields.Selection(
        [
            ("warning", "Warning"),
            ("fine", "Fine"),
            ("suspension", "Suspension"),
            ("exclusion", "Exclusion"),
        ],
        default="warning",
    )

    amount = fields.Float()

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
    )

    note = fields.Html()