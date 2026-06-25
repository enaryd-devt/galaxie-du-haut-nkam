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


class AssociationSubscription(models.Model):
    _name = "association.subscription"
    _description = "Association Subscription"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    # ==========================================================
    # TECHNICAL
    # ==========================================================

    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
    )

    sequence = fields.Integer(
        string="Sequence",
        default=10,
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
    # IDENTIFICATION
    # ==========================================================

    name = fields.Char(
        string="Subscription",
        required=True,
        tracking=True,
    )

    code = fields.Char(
        string="Reference",
        copy=False,
        readonly=True,
        default="New",
        tracking=True,
    )

    description = fields.Text(
        string="Description",
    )

    # ==========================================================
    # INFORMATION
    # ==========================================================

    subscription_type = fields.Selection(
        [
            ("registration", "Registration Fee"),
            ("monthly", "Monthly Fee"),
            ("quarterly", "Quarterly Fee"),
            ("annual", "Annual Fee"),
            ("special", "Special Contribution"),
        ],
        string="Subscription Type",
        required=True,
        default="monthly",
        tracking=True,
    )

    date = fields.Date(
        string="Issue Date",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )

    due_date = fields.Date(
        string="Due Date",
        tracking=True,
    )

    amount = fields.Monetary(
        string="Unit Amount",
        currency_field="currency_id",
        required=True,
        default=0.0,
    )

    # ==========================================================
    # STATUS
    # ==========================================================

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("running", "Running"),
            ("closed", "Closed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ==========================================================
    # RELATIONS
    # ==========================================================

    line_ids = fields.One2many(
        "association.subscription.line",
        "subscription_id",
        string="Subscription Lines",
    )

    line_count = fields.Integer(
        string="Lines",
        compute="_compute_line_count",
    )

    # ==========================================================
    # NOTES
    # ==========================================================

    note = fields.Html(
        string="Internal Notes",
    )

    # ==========================================================
    # COMPUTE
    # ==========================================================

    def _compute_line_count(self):
        for record in self:
            record.line_count = len(record.line_ids)