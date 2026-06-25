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


class AssociationPayment(models.Model):
    _name = "association.payment"
    _description = "Association Payment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "payment_date desc, id desc"

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
        string="Payment Reference",
        required=True,
        tracking=True,
    )

    description = fields.Text(
        string="Description",
    )

    # ==========================================================
    # MEMBER
    # ==========================================================

    member_id = fields.Many2one(
        "association.member",
        string="Member",
        required=True,
        tracking=True,
        ondelete="restrict",
    )

    subscription_id = fields.Many2one(
        "association.subscription",
        string="Subscription",
        tracking=True,
    )

    # ==========================================================
    # PAYMENT
    # ==========================================================

    payment_date = fields.Date(
        string="Payment Date",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )

    amount = fields.Monetary(
        string="Amount",
        currency_field="currency_id",
        default=0.0,
        required=True,
    )

    payment_method = fields.Selection(
        [
            ("cash", "Cash"),
            ("bank", "Bank Transfer"),
            ("cheque", "Cheque"),
            ("mobile_money", "Mobile Money"),
            ("other", "Other"),
        ],
        string="Payment Method",
        default="cash",
        tracking=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
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
        "association.payment.line",
        "payment_id",
        string="Payment Lines",
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