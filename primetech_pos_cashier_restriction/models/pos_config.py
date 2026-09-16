from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv.expression import OR


class PosConfig(models.Model):
    _inherit = "pos.config"

    restricted_employee_ids = fields.Many2many(
        "hr.employee", "pos_config_restricted_employee_rel", "config_id", "employee_id",
        string="Caissiers restreints",
    )
    order_access_employee_ids = fields.Many2many(
        "hr.employee", "pos_config_order_access_employee_rel", "config_id", "employee_id",
        string="Commandes sans remboursement",
    )
    refund_manager_employee_ids = fields.Many2many(
        "hr.employee", "pos_config_refund_manager_employee_rel", "config_id", "employee_id",
        string="Responsables / remboursement",
    )

    def _employee_domain(self, user_id):
        domain = super()._employee_domain(user_id)
        self.ensure_one()
        employee_ids = (
            self.restricted_employee_ids
            | self.order_access_employee_ids
            | self.refund_manager_employee_ids
        ).ids
        return OR([domain, [("id", "in", employee_ids)]]) if employee_ids else domain

    @api.constrains(
        "restricted_employee_ids", "order_access_employee_ids", "refund_manager_employee_ids"
    )
    def _check_employee_access_groups(self):
        for config in self:
            groups = (
                config.restricted_employee_ids,
                config.order_access_employee_ids,
                config.refund_manager_employee_ids,
            )
            employee_ids = [employee.id for group in groups for employee in group]
            if len(employee_ids) != len(set(employee_ids)):
                raise ValidationError(
                    _("Un employe ne peut appartenir qu'a un seul niveau d'acces POS.")
                )
