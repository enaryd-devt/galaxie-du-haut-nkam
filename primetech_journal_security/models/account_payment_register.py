from odoo import _, models
from odoo.exceptions import ValidationError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _get_batch_available_journals(self, batch_result):

        journals = super()._get_batch_available_journals(batch_result)

        user = self.env.user

        if user.has_group("base.group_system"):
            return journals

        return journals.filtered(
            lambda j: user in j.allowed_user_ids
        )

    def action_create_payments(self):

        for wizard in self:

            journal = wizard.journal_id

            if (
                not self.env.user.has_group("base.group_system")
                and self.env.user not in journal.allowed_user_ids
            ):
                raise ValidationError(
                    _("Vous n'êtes pas autorisé à utiliser le journal %s")
                    % journal.display_name
                )

        return super().action_create_payments()