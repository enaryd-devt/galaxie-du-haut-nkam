from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    # Legacy fields are retained only to let existing databases update cleanly.
    # Access decisions are now made exclusively from the active POS employee.
    pos_restricted_cashier = fields.Boolean(string="Ancien droit POS restreint")
    pos_refund_manager = fields.Boolean(string="Ancien droit POS remboursement")
