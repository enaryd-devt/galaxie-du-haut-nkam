# -*- coding: utf-8 -*-

from odoo import fields, models


class AssociationFund(models.Model):
    _name = "association.fund"
    _description = "Association Fund"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    active = fields.Boolean(default=True)

    name = fields.Char(
        required=True,
    )

    description = fields.Text()

    balance = fields.Float()

    state = fields.Selection(
        [
            ("active", "Active"),
            ("closed", "Closed"),
        ],
        default="active",
    )

    note = fields.Html()