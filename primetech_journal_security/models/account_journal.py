from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    allowed_user_ids = fields.Many2many(
        "res.users",
        "account_journal_allowed_user_rel",
        "journal_id",
        "user_id",
        string="Utilisateurs autorisés",
    )

    @api.model
    def _journal_security_domain(self):
        user = self.env.user

        if user.has_group("base.group_system"):
            return []

        return [
            ("allowed_user_ids", "in", user.id),
        ]