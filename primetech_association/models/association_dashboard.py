# -*- coding: utf-8 -*-

##############################################################################
#
#    PrimeTech Association Management
#
##############################################################################

from odoo import fields, models


class AssociationDashboard(models.TransientModel):
    _name = "association.dashboard"
    _description = "Association Dashboard"

    member_count = fields.Integer(
        string="Members",
        default=0,
    )

    active_member_count = fields.Integer(
        string="Active Members",
        default=0,
    )

    subscription_count = fields.Integer(
        string="Subscriptions",
        default=0,
    )

    payment_count = fields.Integer(
        string="Payments",
        default=0,
    )

    meeting_count = fields.Integer(
        string="Meetings",
        default=0,
    )

    donation_count = fields.Integer(
        string="Donations",
        default=0,
    )

    income = fields.Float(
        string="Income",
        default=0.0,
    )

    expense = fields.Float(
        string="Expense",
        default=0.0,
    )

    balance = fields.Float(
        string="Balance",
        default=0.0,
    )