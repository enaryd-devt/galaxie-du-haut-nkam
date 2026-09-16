from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """Reserve selected sources before Odoo checks whether validation is possible."""
        moves_to_assign = self.move_ids.filtered(
            lambda move: move.source_location_id and move.state in ('confirmed', 'waiting', 'partially_available')
        )
        if moves_to_assign:
            moves_to_assign._action_assign()
        return super().button_validate()

    def write(self, vals):
        result = super().write(vals)
        if any(field in vals for field in ('location_id', 'picking_type_id', 'company_id')):
            for picking in self:
                moves = picking.move_ids.filtered(lambda move: move.source_location_id)
                invalid_moves = moves.filtered(lambda move: not move._source_location_is_allowed())
                for move in invalid_moves:
                    move.source_location_id = move._best_source_location()
                (moves | invalid_moves)._sync_source_location()
        return result
