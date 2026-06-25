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


class AssociationPaymentLine(models.Model):
    _name = "association.payment.line"
    _description = "Association Payment Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id"

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

    payment_id = fields.Many2one(
        "association.payment",
        string="Payment",
        required=True,
        ondelete="cascade",
        tracking=True,
    )

    subscription_line_id = fields.Many2one(
        "association.subscription.line",
        string="Subscription Line",
        required=True,
        ondelete="restrict",
        tracking=True,
    )

    member_id = fields.Many2one(
        related="subscription_line_id.member_id",
        string="Member",
        readonly=True,
        store=True,
    )

    subscription_id = fields.Many2one(
        related="subscription_line_id.subscription_id",
        string="Subscription",
        readonly=True,
        store=True,
    )

    # ==========================================================
    # AMOUNTS
    # ==========================================================

    amount_due = fields.Monetary(
        related="subscription_line_id.amount_due",
        string="Amount Due",
        currency_field="currency_id",
        readonly=True,
        store=True,
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
    # STATUS
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

    # ==========================================================
    # NOTES
    # ==========================================================

    note = fields.Html(
        string="Internal Notes",
    )