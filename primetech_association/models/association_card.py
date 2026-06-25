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


class AssociationCard(models.Model):
    _name = "association.card"
    _description = "Association Member Card"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "issue_date desc, id desc"

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

    # ==========================================================
    # IDENTIFICATION
    # ==========================================================

    name = fields.Char(
        string="Card Number",
        required=True,
        tracking=True,
    )

    member_id = fields.Many2one(
        "association.member",
        string="Member",
        required=True,
        tracking=True,
        ondelete="cascade",
    )

    issue_date = fields.Date(
        string="Issue Date",
        default=fields.Date.context_today,
    )

    expiry_date = fields.Date(
        string="Expiry Date",
    )

    qr_code = fields.Binary(
        string="QR Code",
        attachment=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("expired", "Expired"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    note = fields.Html(
        string="Internal Notes",
    )