from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_restricted_employee_ids = fields.Many2many(
        related="pos_config_id.restricted_employee_ids",
        readonly=False,
    )
    pos_order_access_employee_ids = fields.Many2many(
        related="pos_config_id.order_access_employee_ids",
        readonly=False,
    )
    pos_refund_manager_employee_ids = fields.Many2many(
        related="pos_config_id.refund_manager_employee_ids",
        readonly=False,
    )
