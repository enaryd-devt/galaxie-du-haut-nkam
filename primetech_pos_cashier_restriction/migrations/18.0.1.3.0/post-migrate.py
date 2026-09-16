from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    xmlids = (
        "primetech_pos_cashier_restriction.rule_pos_order_restricted_cashier_current_session",
        "primetech_pos_cashier_restriction.rule_pos_order_manager_unrestricted",
        "primetech_pos_cashier_restriction.rule_pos_order_line_restricted_cashier_current_session",
        "primetech_pos_cashier_restriction.rule_pos_order_line_manager_unrestricted",
        "primetech_pos_cashier_restriction.rule_pos_payment_restricted_cashier_current_session",
        "primetech_pos_cashier_restriction.rule_pos_payment_manager_unrestricted",
        "primetech_pos_cashier_restriction.group_pos_restricted_cashier",
        "primetech_pos_cashier_restriction.group_pos_refund_manager",
        "primetech_pos_cashier_restriction.view_users_form_pos_cashier_restriction",
    )
    for xmlid in xmlids:
        record = env.ref(xmlid, raise_if_not_found=False)
        if record:
            record.unlink()
