from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    source_location_id = fields.Many2one(
        'stock.location',
        string='Emplacement source',
        check_company=True,
        index=True,
        help='Emplacement interne réellement utilisé pour prélever cette ligne.',
    )
    source_available_qty = fields.Float(
        string='Disponible',
        compute='_compute_source_available_qty',
        digits='Product Unit of Measure',
        readonly=True,
        help='Quantité disponible du produit dans l’emplacement source sélectionné.',
    )
    allowed_source_location_ids = fields.Many2many(
        'stock.location',
        compute='_compute_allowed_source_location_ids',
        string='Emplacements source autorisés',
    )

    def _source_default_location(self):
        self.ensure_one()
        return self.picking_id.location_id or self.picking_type_id.default_location_src_id

    def _source_scope_location(self):
        """Return the warehouse perimeter while preserving the picking source as fallback."""
        self.ensure_one()
        default_location = self._source_default_location()
        if not default_location or default_location.usage != 'internal':
            return self.env['stock.location']
        warehouse = default_location.warehouse_id or self.picking_type_id.warehouse_id
        return warehouse.view_location_id if warehouse else default_location

    def _source_location_is_allowed(self, location=None):
        self.ensure_one()
        location = location or self.source_location_id
        scope = self._source_scope_location()
        if not location:
            return True
        return bool(
            scope
            and location.usage == 'internal'
            and location._child_of(scope)
            and (not location.company_id or location.company_id == self.company_id)
        )

    @api.depends('picking_id.location_id', 'picking_type_id.default_location_src_id', 'company_id')
    def _compute_allowed_source_location_ids(self):
        Location = self.env['stock.location']
        grouped_moves = defaultdict(lambda: self.env['stock.move'])
        for move in self:
            scope = move._source_scope_location()
            key = (scope.id if scope else False, move.company_id.id)
            grouped_moves[key] |= move
        for (root_id, company_id), moves in grouped_moves.items():
            if not root_id:
                moves.allowed_source_location_ids = False
                continue
            locations = Location.search([
                ('id', 'child_of', root_id),
                ('usage', '=', 'internal'),
                ('company_id', 'in', [False, company_id]),
            ])
            moves.allowed_source_location_ids = locations

    @api.depends('product_id', 'product_uom', 'source_location_id', 'company_id')
    def _compute_source_available_qty(self):
        Quant = self.env['stock.quant']
        for move in self:
            if not move.product_id or not move.source_location_id:
                move.source_available_qty = 0.0
                continue
            available = Quant.with_company(move.company_id)._get_available_quantity(
                move.product_id, move.source_location_id, strict=True,
            )
            move.source_available_qty = move.product_id.uom_id._compute_quantity(
                available, move.product_uom or move.product_id.uom_id,
            )

    def _best_source_location(self):
        self.ensure_one()
        locations = self.allowed_source_location_ids
        default_location = self._source_default_location()
        if not self.product_id or not locations:
            return default_location if self._source_location_is_allowed(default_location) else False
        quantities = self.env['stock.quant'].read_group(
            [
                ('product_id', '=', self.product_id.id),
                ('location_id', 'in', locations.ids),
                ('company_id', 'in', [False, self.company_id.id]),
            ],
            ['quantity:sum', 'reserved_quantity:sum'],
            ['location_id'],
            lazy=False,
        )
        available_by_location = {
            group['location_id'][0]: (group.get('quantity', 0.0) or 0.0) - (group.get('reserved_quantity', 0.0) or 0.0)
            for group in quantities if group.get('location_id')
        }
        requested = self.product_uom._compute_quantity(
            self.product_uom_qty, self.product_id.uom_id,
        ) if self.product_uom else self.product_uom_qty
        candidates = [
            (available_by_location.get(location.id, 0.0), location)
            for location in locations
            if available_by_location.get(location.id, 0.0) > 0.0
        ]
        if candidates:
            # A location covering the whole demand wins; otherwise choose the best stock level.
            candidates.sort(key=lambda item: (item[0] >= requested, item[0], -item[1].id), reverse=True)
            return candidates[0][1]
        return default_location if self._source_location_is_allowed(default_location) else False

    def _sync_source_location(self):
        for move in self:
            if move.source_location_id and move.location_id != move.source_location_id:
                move.with_context(primetech_source_location_sync=True).write({
                    'location_id': move.source_location_id.id,
                })

    @api.onchange('product_id', 'product_uom_qty', 'product_uom', 'picking_id', 'picking_type_id')
    def _onchange_source_location_auto_select(self):
        for move in self:
            source = move._best_source_location()
            move.source_location_id = source
            if source:
                move.location_id = source

    @api.onchange('source_location_id')
    def _onchange_source_location(self):
        for move in self:
            if move.source_location_id and move._source_location_is_allowed():
                move.location_id = move.source_location_id

    @api.constrains('source_location_id', 'picking_id', 'picking_type_id', 'company_id')
    def _check_source_location_id(self):
        for move in self:
            if move.source_location_id and not move._source_location_is_allowed():
                raise ValidationError(_(
                    'L’emplacement source doit être un emplacement interne de la zone source autorisée par ce transfert et de la même société.'
                ))

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            if not move.source_location_id:
                move.source_location_id = move._best_source_location()
        moves._sync_source_location()
        return moves

    def write(self, vals):
        if self.env.context.get('primetech_source_location_sync'):
            return super().write(vals)
        moves_to_reassign = self.filtered(
            lambda move: 'source_location_id' in vals and move.state in ('assigned', 'partially_available')
        )
        if moves_to_reassign:
            moves_to_reassign._do_unreserve()
        result = super().write(vals)
        if 'source_location_id' in vals:
            self._sync_source_location()
            # A manual picking type does not reserve automatically at confirmation.
            # Once a source is explicitly chosen, reserve it immediately from that source.
            self.filtered(
                lambda move: move.source_location_id and move.state in ('confirmed', 'waiting', 'partially_available')
            )._action_assign()
        if any(field in vals for field in ('picking_id', 'picking_type_id', 'company_id')):
            for move in self:
                if move.source_location_id and not move._source_location_is_allowed():
                    move.source_location_id = move._best_source_location()
            self._sync_source_location()
        if moves_to_reassign:
            moves_to_reassign._action_assign()
        return result

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        if self.source_location_id:
            vals['location_id'] = self.source_location_id.id
        return vals

    def _update_reserved_quantity(self, need, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        if self.source_location_id:
            location_id = self.source_location_id
            strict = True
        return super()._update_reserved_quantity(
            need, location_id, lot_id=lot_id, package_id=package_id,
            owner_id=owner_id, strict=strict,
        )

    def _action_done(self, cancel_backorder=False):
        for move in self.filtered('source_location_id'):
            invalid_lines = move.move_line_ids.filtered(
                lambda line: line.location_id != move.source_location_id
            )
            if invalid_lines:
                invalid_lines.with_context(primetech_skip_source_location_check=True).write({
                    'location_id': move.source_location_id.id,
                })
        return super()._action_done(cancel_backorder=cancel_backorder)
