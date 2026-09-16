import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

REFUND_DENIED_MESSAGE = "Vous n’êtes pas autorisé à effectuer des remboursements."
HISTORY_DENIED_MESSAGE = "Vous n’êtes pas autorisé à consulter les anciennes commandes."

ACTIVE_SESSION_STATES = ("opening_control", "opened", "closing_control")


class PosRestrictionAudit(models.Model):
    _name = "pos.restriction.audit"
    _description = "POS Restriction Audit"
    _order = "date desc, id desc"

    user_id = fields.Many2one("res.users", string="Utilisateur", required=True, index=True)
    employee_id = fields.Integer(
        string="Employé POS",
        help="ID technique hr.employee lorsque le module pos_hr est installé.",
    )
    action = fields.Selection(
        [
            ("refund_attempt", "Tentative de remboursement"),
            ("history_access_attempt", "Tentative d'accès historique"),
            ("reprint_attempt", "Tentative de réimpression"),
        ],
        required=True,
        index=True,
    )
    pos_order_id = fields.Many2one("pos.order", string="Commande POS", ondelete="set null")
    session_id = fields.Many2one("pos.session", string="Session POS", ondelete="set null")
    date = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    details = fields.Text()


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _get_pos_order_payload(self, order_data):
        """Return the exported order for both supported ``sync_from_ui`` payloads.

        POS clients send the order directly in some flows, while queued orders are
        wrapped in a mapping containing a ``data`` key.  Security checks must
        always inspect the exported order, rather than the transport envelope.
        """
        if isinstance(order_data, dict) and isinstance(order_data.get("data"), dict):
            return order_data["data"]
        return order_data or {}

    def _get_pos_order_session(self, order_data=None, vals=None, order=None):
        if order:
            return order.session_id
        data = self._get_pos_order_payload(order_data or vals)
        session_id = data.get("session_id")
        if isinstance(session_id, (list, tuple)):
            session_id = session_id[0] if session_id else False
        return self.env["pos.session"].browse(session_id).exists() if session_id else self.env["pos.session"]

    def _get_pos_order_config(self, order_data=None, vals=None, order=None, config=None):
        if config:
            return config
        session = self._get_pos_order_session(order_data=order_data, vals=vals, order=order)
        if session:
            return session.config_id
        config_id = self._get_pos_order_payload(order_data or vals).get("config_id")
        return self.env["pos.config"].browse(config_id).exists() if config_id else self.env["pos.config"]

    def _get_pos_order_employee(self, order_data=None, vals=None, order=None):
        if "hr.employee" not in self.env.registry.models:
            return False
        if order and "employee_id" in order._fields:
            return order.employee_id
        data = self._get_pos_order_payload(order_data or vals)
        employee_id = data.get("employee_id")
        if isinstance(employee_id, (list, tuple)):
            employee_id = employee_id[0] if employee_id else False
        return self.env["hr.employee"].browse(employee_id).exists() if employee_id else False

    def _pos_employee_is_manager(self, employee, config):
        return bool(employee and config and employee in config.refund_manager_employee_ids)

    def _pos_employee_is_refund_restricted_cashier(self, employee, config):
        return bool(
            employee
            and config
            and (
                employee in config.restricted_employee_ids
                or employee in config.order_access_employee_ids
            )
        )

    def _pos_employee_is_history_restricted_cashier(self, employee, config):
        return bool(
            employee
            and config
            and employee in config.restricted_employee_ids
        )

    @api.model
    def _extract_pos_line_vals(self, commands):
        for command in commands or []:
            if isinstance(command, dict):
                yield command
            elif isinstance(command, (list, tuple)) and len(command) >= 3 and command[0] in (0, 1):
                yield command[2] or {}

    @api.model
    def _pos_line_vals_are_refund(self, vals):
        if vals.get("refunded_orderline_id"):
            return True
        try:
            return float(vals.get("qty") or 0.0) < 0.0
        except (TypeError, ValueError):
            return False

    @api.model
    def _pos_order_vals_are_refund(self, vals):
        if any(self._pos_line_vals_are_refund(line_vals) for line_vals in self._extract_pos_line_vals(vals.get("lines"))):
            return True
        try:
            return float(vals.get("amount_total") or 0.0) < 0.0
        except (TypeError, ValueError):
            return False

    def _pos_refund_restriction_applies(self, order_data=None, vals=None, order=None):
        if self.env.context.get("primetech_skip_pos_cashier_restriction"):
            return False
        config = self._get_pos_order_config(order_data=order_data, vals=vals, order=order)
        employee = self._get_pos_order_employee(order_data=order_data, vals=vals, order=order)
        return self._pos_employee_is_refund_restricted_cashier(employee, config)

    def _log_pos_restriction_attempt(self, action, order=None, session=None, details=None, employee=None):
        employee = employee or self._get_pos_order_employee(order=order)
        session = session or (order.session_id if order else self.env["pos.session"])
        order_name = order.display_name if order else "-"
        _logger.warning(
            "Utilisateur %s a tenté une action POS interdite (%s). Commande: %s. Session: %s.",
            self.env.user.display_name,
            action,
            order_name,
            session.display_name if session else "-",
        )
        self.env["pos.restriction.audit"].sudo().create({
            "user_id": self.env.user.id,
            "employee_id": employee.id if employee else False,
            "action": action,
            "pos_order_id": order.id if order else False,
            "session_id": session.id if session else False,
            "details": details or "",
        })

    def _check_pos_refund_rights(self, order_data=None, vals=None, order=None, action="refund_attempt"):
        target_order = order or (self if self._name == "pos.order" and len(self) == 1 else False)
        if not self._pos_refund_restriction_applies(order_data=order_data, vals=vals, order=target_order):
            return True
        employee = self._get_pos_order_employee(order_data=order_data, vals=vals, order=target_order)
        session = self._get_pos_order_session(order_data=order_data, vals=vals, order=target_order)
        self._log_pos_restriction_attempt(
            action,
            order=target_order,
            session=session,
            employee=employee,
            details=str(order_data or vals or ""),
        )
        raise UserError(_(REFUND_DENIED_MESSAGE))

    def _check_pos_history_rights(self, config=None, session=None, order=None, action="history_access_attempt"):
        config = config or self._get_pos_order_config(order=order)
        session = session or (order.session_id if order else self.env["pos.session"])
        if self.env.context.get("primetech_skip_pos_cashier_restriction"):
            return True
        employee = self._get_pos_order_employee(order=order) or (session.employee_id if session and "employee_id" in session._fields else False)
        restricted = self._pos_employee_is_history_restricted_cashier(employee, config)
        if not restricted:
            return True
        self._log_pos_restriction_attempt(action, order=order, session=session, employee=employee)
        raise UserError(_(HISTORY_DENIED_MESSAGE))

    def _restricted_cashier_can_use_order(self, order):
        return (
            order.user_id == self.env.user
            and order.session_id.state in ACTIVE_SESSION_STATES
            and order.company_id in self.env.user.company_ids
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self._pos_order_vals_are_refund(vals):
                self._check_pos_refund_rights(vals=vals)
        return super().create(vals_list)

    def write(self, vals):
        if self._pos_order_vals_are_refund(vals):
            for order in self:
                self._check_pos_refund_rights(vals=vals, order=order)
        return super().write(vals)

    @api.model
    def sync_from_ui(self, orders):
        for order_data in orders:
            order_vals = self._get_pos_order_payload(order_data)
            if self._pos_order_vals_are_refund(order_vals):
                self._check_pos_refund_rights(order_data=order_data)
        return super().sync_from_ui(orders)

    def _refund(self):
        for order in self:
            order._check_pos_refund_rights(order=order)
        return super()._refund()

    @api.model
    def search_paid_order_ids(self, config_id, domain, limit, offset):
        config = self.env["pos.config"].browse(config_id).exists()
        self._check_pos_history_rights(config=config, session=config.current_session_id)
        return super().search_paid_order_ids(config_id, domain, limit, offset)

    def action_send_receipt(self, email, ticket_image, basic_image):
        for order in self:
            if (
                order.state != "draft"
                and self._pos_employee_is_history_restricted_cashier(
                    order.employee_id, order.session_id.config_id
                )
                and not self._restricted_cashier_can_use_order(order)
            ):
                order._check_pos_history_rights(order=order, action="reprint_attempt")
        return super().action_send_receipt(email, ticket_image, basic_image)


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    @api.model_create_multi
    def create(self, vals_list):
        pos_order = self.env["pos.order"]
        for vals in vals_list:
            if pos_order._pos_line_vals_are_refund(vals):
                order = self.env["pos.order"].browse(vals.get("order_id")).exists()
                pos_order._check_pos_refund_rights(vals=vals, order=order)
        return super().create(vals_list)

    def write(self, vals):
        if self.env["pos.order"]._pos_line_vals_are_refund(vals):
            for line in self:
                self.env["pos.order"]._check_pos_refund_rights(vals=vals, order=line.order_id)
        return super().write(vals)
