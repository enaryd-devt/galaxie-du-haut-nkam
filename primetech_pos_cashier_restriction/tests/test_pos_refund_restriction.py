from odoo import Command
from odoo.addons.point_of_sale.tests.common import TestPointOfSaleCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPosRefundRestriction(TestPointOfSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cashier = cls.env["hr.employee"].create({
            "name": "Orders Without Refund",
            "company_id": cls.company.id,
        })
        cls.manager = cls.env["hr.employee"].create({
            "name": "Refund Manager",
            "company_id": cls.company.id,
        })
        cls.unassigned = cls.env["hr.employee"].create({
            "name": "Unassigned Cashier",
            "company_id": cls.company.id,
        })

    def test_only_refund_manager_employee_can_refund(self):
        self.pos_config.write({
            "module_pos_hr": True,
            "order_access_employee_ids": [Command.link(self.cashier.id)],
            "refund_manager_employee_ids": [Command.link(self.manager.id)],
        })
        orders = self.env["pos.order"]
        self.assertTrue(orders._pos_employee_is_refund_restricted_cashier(self.cashier, self.pos_config))
        self.assertFalse(orders._pos_employee_is_refund_restricted_cashier(self.manager, self.pos_config))
        self.assertFalse(orders._pos_employee_is_refund_restricted_cashier(self.unassigned, self.pos_config))
