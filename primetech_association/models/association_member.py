# -*- coding: utf-8 -*-

##############################################################################
#
#    PrimeTech Association Management
#    Copyright (C) 2026 PrimeTech Services.
#    Author: PrimeTech Services
#    License LGPL-3
#
##############################################################################

from odoo import fields, models


class AssociationMember(models.Model):
    _name = "association.member"
    _description = "Association Member"
    _inherit = ["mail.thread", "mail.activity.mixin", "image.mixin"]
    _order = "name"

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
        string="Color",
    )

    # ==========================================================
    # IDENTIFICATION
    # ==========================================================

    name = fields.Char(
        string="Member Name",
        required=True,
        tracking=True,
    )

    member_code = fields.Char(
        string="Member Number",
        copy=False,
        readonly=True,
        default="New",
        tracking=True,
    )

    first_name = fields.Char(
        string="First Name",
    )

    last_name = fields.Char(
        string="Last Name",
    )

    # ==========================================================
    # PERSONAL INFORMATION
    # ==========================================================

    gender = fields.Selection(
        [
            ("male", "Male"),
            ("female", "Female"),
        ],
        string="Gender",
    )

    birth_date = fields.Date(
        string="Birth Date",
    )

    birth_place = fields.Char(
        string="Birth Place",
    )

    profession = fields.Char(
        string="Profession",
    )

    marital_status = fields.Selection(
        [
            ("single", "Single"),
            ("married", "Married"),
            ("divorced", "Divorced"),
            ("widowed", "Widowed"),
        ],
        string="Marital Status",
    )

    # ==========================================================
    # CONTACT
    # ==========================================================

    phone = fields.Char(
        string="Phone",
    )

    mobile = fields.Char(
        string="Mobile",
    )

    email = fields.Char(
        string="Email",
    )

    website = fields.Char(
        string="Website",
    )

    # ==========================================================
    # ADDRESS
    # ==========================================================

    street = fields.Char(
        string="Street",
    )

    street2 = fields.Char(
        string="Street 2",
    )

    city = fields.Char(
        string="City",
    )

    zip = fields.Char(
        string="ZIP",
    )

    country_id = fields.Many2one(
        "res.country",
        string="Country",
    )

    state_id = fields.Many2one(
        "res.country.state",
        string="State",
    )

    # ==========================================================
    # ASSOCIATION
    # ==========================================================

    category_id = fields.Many2one(
        "association.member.category",
        string="Category",
    )

    function_id = fields.Many2one(
        "association.member.function",
        string="Function",
    )

    join_date = fields.Date(
        string="Join Date",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("resigned", "Resigned"),
            ("excluded", "Excluded"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ==========================================================
    # DOCUMENTS
    # ==========================================================

    id_card_number = fields.Char(
        string="National ID Number",
    )

    passport_number = fields.Char(
        string="Passport Number",
    )

    # ==========================================================
    # STATISTICS (PLACEHOLDERS)
    # ==========================================================

    payment_count = fields.Integer(
        string="Payments",
        default=0,
    )

    subscription_count = fields.Integer(
        string="Subscriptions",
        default=0,
    )

    meeting_count = fields.Integer(
        string="Meetings",
        default=0,
    )

    attendance_count = fields.Integer(
        string="Attendances",
        default=0,
    )

    donation_count = fields.Integer(
        string="Donations",
        default=0,
    )

    penalty_count = fields.Integer(
        string="Penalties",
        default=0,
    )

    # ==========================================================
    # NOTES
    # ==========================================================

    note = fields.Html(
        string="Notes",
    )