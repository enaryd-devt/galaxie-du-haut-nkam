# Copyright 2013-2014 Camptocamp SA - Guewen Baconnier
# © 2016 ForgeFlow, S.L.
# © 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.base.tests.common import BaseCommon


class TestSaleSourcedByLine(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order_model = cls.env["sale.order"]
        cls.sale_order_line_model = cls.env["sale.order.line"]
        cls.stock_move_model = cls.env["stock.move"]
        cls.stock_warehouse_model = cls.env["stock.warehouse"]

        # Refs
        cls.customer = cls.env.ref("base.res_partner_2")
        cls.product_1 = cls.env.ref("product.product_product_27")
        cls.product_2 = cls.env.ref("product.product_product_24")
        cls.warehouse0 = cls.env.ref("stock.warehouse0")
        cls.warehouse1 = cls.stock_warehouse_model.create(
            {"name": "Test Warehouse", "code": "TWH"}
        )

    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param(
            "sale_sourced_by_line.excluded_auto_warehouse_id", False
        )

    def test_sales_order_multi_source(self):
        so = self.sale_order_model.create(
            {
                "partner_id": self.customer.id,
            }
        )
        self.sale_order_line_model.create(
            {
                "product_id": self.product_1.id,
                "product_uom_qty": 8,
                "warehouse_id": self.warehouse1.id,
                "order_id": so.id,
            }
        )
        self.sale_order_line_model.create(
            {
                "product_id": self.product_2.id,
                "product_uom_qty": 8,
                "warehouse_id": self.warehouse0.id,
                "order_id": so.id,
            }
        )
        # confirm quotation
        so.action_confirm()
        self.assertEqual(
            len(so.picking_ids),
            2,
            f"2 delivery orders expected. Got {len(so.picking_ids)} instead",
        )
        for line in so.order_line:
            self.assertEqual(
                line.procurement_group_id.name,
                line.order_id.name + "/" + line.warehouse_id.name,
                "The name of the procurement group is not " "correct.",
            )
            moves = self.stock_move_model.search(
                [("group_id", "=", line.procurement_group_id.id)]
            )
            for move in moves:
                self.assertEqual(
                    move.group_id,
                    line.procurement_group_id,
                    "The group in the stock move does not "
                    "match with the procurement group in "
                    "the sales order line.",
                )
                self.assertEqual(
                    move.picking_id.group_id,
                    line.procurement_group_id,
                    "The group in the stock picking does "
                    "not match with the procurement group "
                    "in the sales order line.",
                )

    def test_sales_order_no_source(self):
        so = self.sale_order_model.create(
            {
                "partner_id": self.customer.id,
                "warehouse_id": self.warehouse1.id,
            }
        )
        self.sale_order_line_model.create(
            {"product_id": self.product_1.id, "product_uom_qty": 8, "order_id": so.id}
        )
        self.sale_order_line_model.create(
            {"product_id": self.product_2.id, "product_uom_qty": 8, "order_id": so.id}
        )
        # confirm quotation
        so.action_confirm()
        self.assertEqual(
            len(so.picking_ids),
            1,
            f"1 delivery order expected. Got {len(so.picking_ids)} instead",
        )

    def test_sale_order_source(self):
        so = self.sale_order_model.create(
            {
                "partner_id": self.customer.id,
            }
        )
        self.sale_order_line_model.create(
            {
                "product_id": self.product_1.id,
                "product_uom_qty": 8,
                "warehouse_id": self.warehouse1.id,
                "order_id": so.id,
            }
        )
        self.sale_order_line_model.create(
            {
                "product_id": self.product_2.id,
                "product_uom_qty": 8,
                "warehouse_id": self.warehouse0.id,
                "order_id": so.id,
            }
        )
        # confirm quotation
        so.action_confirm()
        for line in so.order_line:
            moves = self.stock_move_model.search(
                [("group_id", "=", line.procurement_group_id.id)]
            )
            for move in moves:
                self.assertEqual(
                    move.warehouse_id,
                    line.warehouse_id,
                    "The warehouse in the stock move does not "
                    "match with the Sales order line.",
                )

    def test_best_warehouse_ignores_configured_excluded_warehouse(self):
        self.env["stock.quant"]._update_available_quantity(
            self.product_1, self.warehouse0.lot_stock_id, 10
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product_1, self.warehouse1.lot_stock_id, 3
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "sale_sourced_by_line.excluded_auto_warehouse_id", self.warehouse0.id
        )
        so = self.sale_order_model.create({"partner_id": self.customer.id})
        line = self.sale_order_line_model.create(
            {
                "product_id": self.product_1.id,
                "product_uom_qty": 1,
                "order_id": so.id,
            }
        )

        self.assertEqual(line.warehouse_id, self.warehouse1)

    def test_product_selection_forces_warehouse_with_highest_available_qty(self):
        warehouse2 = self.stock_warehouse_model.create(
            {"name": "Best Stock Warehouse", "code": "BSW"}
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product_1, self.warehouse0.lot_stock_id, 20
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product_1, self.warehouse1.lot_stock_id, 3
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product_1, warehouse2.lot_stock_id, 12
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "sale_sourced_by_line.excluded_auto_warehouse_id", self.warehouse0.id
        )
        so = self.sale_order_model.create({"partner_id": self.customer.id})
        line = self.sale_order_line_model.create(
            {
                "product_id": self.product_1.id,
                "product_uom_qty": 1,
                "warehouse_id": self.warehouse1.id,
                "order_id": so.id,
            }
        )

        self.assertEqual(line.warehouse_id, warehouse2)

    def test_product_selection_falls_back_to_order_warehouse_without_stock(self):
        product = self.env["product.product"].create({"name": "Product Without Stock"})
        so = self.sale_order_model.create(
            {"partner_id": self.customer.id, "warehouse_id": self.warehouse1.id}
        )
        line = self.sale_order_line_model.new(
            {
                "product_id": product.id,
                "product_uom_qty": 1,
                "order_id": so.id,
            }
        )

        result = line._onchange_product_set_best_warehouse()

        self.assertEqual(line.warehouse_id, self.warehouse1)
        self.assertEqual(result["value"]["warehouse_id"], self.warehouse1.id)

    def test_product_selection_falls_back_to_allowed_warehouse_when_order_excluded(self):
        product = self.env["product.product"].create({"name": "No Stock Excluded Order"})
        self.env["ir.config_parameter"].sudo().set_param(
            "sale_sourced_by_line.excluded_auto_warehouse_id", self.warehouse0.id
        )
        so = self.sale_order_model.create(
            {"partner_id": self.customer.id, "warehouse_id": self.warehouse0.id}
        )
        line = self.sale_order_line_model.new(
            {
                "product_id": product.id,
                "product_uom_qty": 1,
                "order_id": so.id,
            }
        )

        result = line._onchange_product_set_best_warehouse()

        self.assertTrue(line.warehouse_id)
        self.assertNotEqual(line.warehouse_id, self.warehouse0)
        self.assertEqual(result["value"]["warehouse_id"], line.warehouse_id.id)

    def test_excluded_order_warehouse_is_not_defaulted_on_line(self):
        self.env["stock.quant"]._update_available_quantity(
            self.product_1, self.warehouse0.lot_stock_id, 10
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "sale_sourced_by_line.excluded_auto_warehouse_id", self.warehouse0.id
        )
        so = self.sale_order_model.create(
            {"partner_id": self.customer.id, "warehouse_id": self.warehouse0.id}
        )
        line = self.sale_order_line_model.create(
            {
                "product_id": self.product_1.id,
                "product_uom_qty": 1,
                "order_id": so.id,
            }
        )

        self.assertNotEqual(line.warehouse_id, self.warehouse0)

    def test_excluded_warehouse_can_still_be_selected_manually(self):
        self.env["stock.quant"]._update_available_quantity(
            self.product_1, self.warehouse0.lot_stock_id, 10
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "sale_sourced_by_line.excluded_auto_warehouse_id", self.warehouse0.id
        )
        so = self.sale_order_model.create({"partner_id": self.customer.id})
        line = self.sale_order_line_model.create(
            {
                "product_id": self.product_1.id,
                "product_uom_qty": 1,
                "warehouse_id": self.warehouse0.id,
                "order_id": so.id,
            }
        )

        self.assertEqual(line.warehouse_id, self.warehouse0)
