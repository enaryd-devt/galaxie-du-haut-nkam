# -*- coding: utf-8 -*-

##############################################################################
#
#    PrimeTech Association Management
#    Copyright (C) 2026 PrimeTech Services
#
#    Author: PrimeTech Services
#    License LGPL-3
#
##############################################################################

from odoo import fields, models


class AssociationSubscriptionLine(models.Model):
    _name = "association.subscription.line"
    _description = "Association Subscription Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "member_id"

    # ==========================================================
    # TECHNICAL
    # ==========================================================

    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    currency_id = fields.Many2one(
        related="company_id.currency_id",
        readonly=True,
        store=True,
    )

    color = fields.Integer(
        string="Color Index",
    )

    # ==========================================================
    # RELATIONS
    # ==========================================================

    subscription_id = fields.Many2one(
        "association.subscription",
        string="Subscription",
        required=True,
        ondelete="cascade",
        tracking=True,
    )

    member_id = fields.Many2one(
        "association.member",
        string="Member",
        required=True,
        ondelete="restrict",
        tracking=True,
    )

    category_id = fields.Many2one(
        related="member_id.category_id",
        string="Category",
        readonly=True,
        store=True,
    )

    function_id = fields.Many2one(
        related="member_id.function_id",
        string="Function",
        readonly=True,
        store=True,
    )

    # ==========================================================
    # AMOUNTS
    # ==========================================================

    amount_due = fields.Monetary(
        string="Amount Due",
        currency_field="currency_id",
        default=0.0,
    )

    amount_paid = fields.Monetary(
        string="Amount Paid",
        currency_field="currency_id",
        default=0.0,
    )

    balance = fields.Monetary(
        string="Balance",
        currency_field="currency_id",
        default=0.0,
    )

    # ==========================================================
    # PAYMENT STATUS
    # ==========================================================

    payment_state = fields.Selection(
        [
            ("not_paid", "Not Paid"),
            ("partial", "Partially Paid"),
            ("paid", "Paid"),
        ],
        string="Payment Status",
        default="not_paid",
        tracking=True,
    )

    payment_date = fields.Date(
        string="Last Payment Date",
    )

    # ==========================================================
    # NOTES
    # ==========================================================

    note = fields.Html(
        string="Internal Notes",
    )