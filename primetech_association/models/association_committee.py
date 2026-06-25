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


class AssociationCommittee(models.Model):
    _name = "association.committee"
    _description = "Executive Committee"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date desc, id desc"

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

    color = fields.Integer(
        string="Color Index",
    )

    # ==========================================================
    # IDENTIFICATION
    # ==========================================================

    name = fields.Char(
        string="Mandate",
        required=True,
        tracking=True,
        help="Example: Executive Committee 2026-2029",
    )

    code = fields.Char(
        string="Reference",
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

    function_id = fields.Many2one(
        "association.member.function",
        string="Function",
        required=True,
        tracking=True,
        ondelete="restrict",
    )

    category_id = fields.Many2one(
        related="member_id.category_id",
        string="Category",
        store=True,
        readonly=True,
    )

    # ==========================================================
    # MANDATE
    # ==========================================================

    start_date = fields.Date(
        string="Start Date",
        tracking=True,
    )

    end_date = fields.Date(
        string="End Date",
        tracking=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("running", "Running"),
            ("expired", "Expired"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ==========================================================
    # OPTIONS
    # ==========================================================

    is_signatory = fields.Boolean(
        string="Authorized Signatory",
        default=False,
    )

    is_financial = fields.Boolean(
        string="Financial Authority",
        default=False,
    )

    # ==========================================================
    # NOTES
    # ==========================================================

    note = fields.Html(
        string="Internal Notes",
    )