from odoo import Command
from odoo.addons.point_of_sale.tests.common import TestPointOfSaleCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPosEmployeeAccess(TestPointOfSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.restricted_employee = cls.env["hr.employee"].create({
            "name": "Restricted Cashier",
            "company_id": cls.company.id,
        })
        cls.order_employee = cls.env["hr.employee"].create({
            "name": "Orders Cashier",
            "company_id": cls.company.id,
        })
        cls.refund_employee = cls.env["hr.employee"].create({
            "name": "Refund Manager",
            "company_id": cls.company.id,
        })

    def test_employee_access_groups_are_exclusive(self):
        self.pos_config.write({
            "restricted_employee_ids": [Command.link(self.restricted_employee.id)],
            "order_access_employee_ids": [Command.link(self.order_employee.id)],
            "refund_manager_employee_ids": [Command.link(self.refund_employee.id)],
        })
        self.assertIn(self.restricted_employee, self.pos_config.restricted_employee_ids)
        self.assertIn(self.order_employee, self.pos_config.order_access_employee_ids)
        self.assertIn(self.refund_employee, self.pos_config.refund_manager_employee_ids)
