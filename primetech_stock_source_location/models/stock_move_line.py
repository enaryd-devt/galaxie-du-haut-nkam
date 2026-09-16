from odoo import api, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        """Keep operation lines aligned with the source selected on their move."""
        move_ids = [vals.get('move_id') for vals in vals_list if vals.get('move_id')]
        moves = {move.id: move for move in self.env['stock.move'].browse(move_ids)}
        for vals in vals_list:
            move = moves.get(vals.get('move_id'))
            if move and move.source_location_id:
                vals['location_id'] = move.source_location_id.id
        return super().create(vals_list)

    def write(self, vals):
        if 'location_id' in vals and not self.env.context.get('primetech_skip_source_location_check'):
            protected_lines = self.filtered('move_id.source_location_id')
            if protected_lines:
                # A multi-record write can contain lines belonging to moves with different sources.
                # Keep each line tied to its own selected source.
                for line in self:
                    line_vals = dict(vals)
                    if line.move_id.source_location_id:
                        line_vals['location_id'] = line.move_id.source_location_id.id
                    super(StockMoveLine, line).write(line_vals)
                return True
        return super().write(vals)
