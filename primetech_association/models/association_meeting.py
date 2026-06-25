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


class AssociationMeeting(models.Model):
    _name = "association.meeting"
    _description = "Association Meeting"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "meeting_date desc, id desc"

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
        string="Meeting Title",
        required=True,
        tracking=True,
    )

    reference = fields.Char(
        string="Reference",
        readonly=True,
        copy=False,
        default="New",
        tracking=True,
    )

    description = fields.Text(
        string="Description",
    )

    # ==========================================================
    # MEETING
    # ==========================================================

    meeting_type = fields.Selection(
        [
            ("ordinary", "Ordinary Meeting"),
            ("extraordinary", "Extraordinary Meeting"),
            ("general_assembly", "General Assembly"),
            ("executive", "Executive Committee"),
        ],
        string="Meeting Type",
        default="ordinary",
        required=True,
        tracking=True,
    )

    meeting_date = fields.Date(
        string="Meeting Date",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )

    start_time = fields.Float(
        string="Start Time",
    )

    end_time = fields.Float(
        string="End Time",
    )

    location = fields.Char(
        string="Location",
    )

    organizer_id = fields.Many2one(
        "association.member",
        string="Organizer",
        tracking=True,
    )

    # ==========================================================
    # STATUS
    # ==========================================================

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("planned", "Planned"),
            ("ongoing", "Ongoing"),
            ("done", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ==========================================================
    # ATTENDANCE
    # ==========================================================

    attendance_ids = fields.One2many(
        "association.meeting.attendance",
        "meeting_id",
        string="Attendance",
    )

    attendance_count = fields.Integer(
        string="Attendance",
        compute="_compute_attendance_count",
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

    def _compute_attendance_count(self):
        for record in self:
            record.attendance_count = len(record.attendance_ids)