from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStockSourceLocation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.product = cls.env['product.product'].create({
            'name': 'Produit emplacement source',
            'is_storable': True,
        })
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Entrepôt source',
            'code': 'SRC',
            'company_id': cls.company.id,
            'reception_steps': 'one_step',
            'delivery_steps': 'ship_only',
        })
        cls.location_a = cls.env['stock.location'].create({
            'name': 'Rayon A',
            'location_id': cls.warehouse.lot_stock_id.id,
            'usage': 'internal',
            'company_id': cls.company.id,
        })
        cls.location_b = cls.env['stock.location'].create({
            'name': 'Rayon B',
            'location_id': cls.warehouse.lot_stock_id.id,
            'usage': 'internal',
            'company_id': cls.company.id,
        })
        cls.customer_location = cls.env.ref('stock.stock_location_customers')

    def _add_stock(self, location, quantity):
        self.env['stock.quant']._update_available_quantity(self.product, location, quantity)

    def _new_move(self, quantity=10.0, source_location=None):
        source_location = source_location or self.warehouse.lot_stock_id
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.warehouse.out_type_id.id,
            'location_id': source_location.id,
            'location_dest_id': self.customer_location.id,
        })
        return self.env['stock.move'].create({
            'name': self.product.display_name,
            'picking_id': picking.id,
            'picking_type_id': picking.picking_type_id.id,
            'product_id': self.product.id,
            'product_uom_qty': quantity,
            'product_uom': self.product.uom_id.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })

    def test_01_auto_selects_only_available_sublocation(self):
        self._add_stock(self.location_a, 15.0)
        move = self._new_move()
        self.assertEqual(move.source_location_id, self.location_a)
        self.assertEqual(move.location_id, self.location_a)

    def test_02_auto_selects_location_covering_demand(self):
        self._add_stock(self.location_a, 7.0)
        self._add_stock(self.location_b, 12.0)
        move = self._new_move(10.0)
        self.assertEqual(move.source_location_id, self.location_b)

    def test_03_defaults_to_operation_source_without_stock(self):
        move = self._new_move(10.0)
        self.assertEqual(move.source_location_id, self.warehouse.lot_stock_id)

    def test_04_source_scope_includes_the_entire_warehouse(self):
        move = self._new_move(source_location=self.location_a)
        self.assertIn(self.location_a, move.allowed_source_location_ids)
        self.assertIn(self.location_b, move.allowed_source_location_ids)
        self.assertEqual(move.source_location_id, self.location_a)

    def test_05_manual_source_recomputes_available_quantity(self):
        self._add_stock(self.location_b, 8.0)
        move = self._new_move()
        move.write({'source_location_id': self.location_b.id})
        self.assertEqual(move.source_available_qty, 8.0)
        self.assertEqual(move.location_id, self.location_b)

    def test_06_rejects_location_from_another_warehouse(self):
        other_warehouse = self.env['stock.warehouse'].create({
            'name': 'Autre entrepôt',
            'code': 'OTH',
            'company_id': self.company.id,
            'reception_steps': 'one_step',
            'delivery_steps': 'ship_only',
        })
        move = self._new_move()
        with self.assertRaises(ValidationError):
            move.write({'source_location_id': other_warehouse.lot_stock_id.id})

    def test_07_validation_decrements_selected_location(self):
        self._add_stock(self.location_a, 15.0)
        move = self._new_move(10.0)
        move._action_confirm()
        move._action_assign()
        move.move_line_ids.quantity = 10.0
        move._action_done()
        remaining = self.env['stock.quant']._get_available_quantity(
            self.product, self.location_a, strict=True,
        )
        self.assertEqual(remaining, 5.0)

    def test_08_source_change_reserves_a_confirmed_move(self):
        self._add_stock(self.location_b, 10.0)
        move = self._new_move(10.0)
        move._action_confirm()
        move.write({'source_location_id': self.location_b.id})
        self.assertEqual(move.location_id, self.location_b)
        self.assertTrue(move.move_line_ids)
        self.assertEqual(move.state, 'assigned')

    def test_09_does_not_leak_other_company_location(self):
        other_company = self.env['res.company'].create({'name': 'Société isolée'})
        other_warehouse = self.env['stock.warehouse'].with_company(other_company).create({
            'name': 'Entrepôt isolé',
            'code': 'ISO',
            'company_id': other_company.id,
            'reception_steps': 'one_step',
            'delivery_steps': 'ship_only',
        })
        move = self._new_move()
        self.assertNotIn(other_warehouse.lot_stock_id, move.allowed_source_location_ids)
        with self.assertRaises(ValidationError):
            move.with_context(allowed_company_ids=[self.company.id, other_company.id]).write({
                'source_location_id': other_warehouse.lot_stock_id.id,
            })
