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


class AssociationMeetingAttendance(models.Model):
    _name = "association.meeting.attendance"
    _description = "Association Meeting Attendance"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "meeting_id desc, member_id"

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

    color = fields.Integer(
        string="Color Index",
    )

    # ==========================================================
    # RELATIONS
    # ==========================================================

    meeting_id = fields.Many2one(
        "association.meeting",
        string="Meeting",
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
    # ATTENDANCE
    # ==========================================================

    attendance_state = fields.Selection(
        [
            ("present", "Present"),
            ("absent", "Absent"),
            ("excused", "Excused"),
            ("late", "Late"),
        ],
        string="Attendance Status",
        default="present",
        tracking=True,
        required=True,
    )

    arrival_time = fields.Float(
        string="Arrival Time",
    )

    departure_time = fields.Float(
        string="Departure Time",
    )

    observation = fields.Text(
        string="Observation",
    )

    # ==========================================================
    # NOTES
    # ==========================================================

    note = fields.Html(
        string="Internal Notes",
    )