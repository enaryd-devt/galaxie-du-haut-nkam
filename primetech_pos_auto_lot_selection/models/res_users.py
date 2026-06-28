from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = "res.users"

    is_pos_manager = fields.Boolean(
        compute="_compute_is_pos_manager",
        store=False,
    )

    @api.depends_context("uid")
    def _compute_is_pos_manager(self):

        for user in self:
            user.is_pos_manager = user.has_group(
                "point_of_sale.group_pos_manager"
            )