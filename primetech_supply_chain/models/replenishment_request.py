# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PrimetechReplenishmentRequest(models.Model):
    _name = 'primetech.replenishment.request'
    _description = "Demande de réapprovisionnement"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string="Référence", default="Nouveau", copy=False, readonly=True)

    company_id = fields.Many2one(
        'res.company', string="Société",
        default=lambda self: self.env.company, required=True)

    shop_id = fields.Many2one(
        'primetech.shop', string="Boutique", required=True, tracking=True)

    rayonniste_id = fields.Many2one(
        'res.users', string="Rayonniste", tracking=True,
        default=lambda self: self.env.user, readonly=True)

    responsable_boutique_id = fields.Many2one(
        'res.users', related='shop_id.responsable_boutique_id',
        string="Responsable Boutique", store=True, readonly=True)

    responsable_magasin_id = fields.Many2one(
        'res.users', related='shop_id.responsable_magasin_id',
        string="Responsable Magasin", store=True, readonly=True)

    warehouse_id = fields.Many2one(
        'stock.warehouse', related='shop_id.warehouse_id',
        string="Magasin source", store=True, readonly=True)

    date_request = fields.Datetime(
        string="Date de la demande", default=fields.Datetime.now, readonly=True)
    date_shop_validation = fields.Datetime(
        string="Date validation boutique", readonly=True)
    date_warehouse_validation = fields.Datetime(
        string="Date validation magasin", readonly=True)

    state = fields.Selection([
        ('draft', "Brouillon"),
        ('to_approve_shop', "À traiter (Boutique)"),
        ('to_approve_warehouse', "À traiter (Magasin)"),
        ('approved', "Approuvée - Transfert en cours"),
        ('done', "Terminée"),
        ('refused', "Refusée"),
    ], string="État", default='draft', tracking=True, copy=False)

    line_ids = fields.One2many(
        'primetech.replenishment.line', 'request_id',
        string="Lignes de produits")

    line_count = fields.Integer(compute='_compute_line_count')

    picking_id = fields.Many2one(
        'stock.picking', string="Transfert de stock",
        readonly=True, copy=False)

    picking_state = fields.Selection(
        related='picking_id.state', string="État du transfert")

    note = fields.Text(string="Motif / Commentaire")
    refusal_reason = fields.Text(string="Motif du refus")

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', "Nouveau") == "Nouveau":
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'primetech.replenishment.request') or "Nouveau"
        return super().create(vals_list)

    # ------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------
    def action_submit_to_shop(self):
        """Rayonniste -> soumet au Responsable Boutique."""
        for rec in self:
            if not rec.line_ids:
                raise UserError(_(
                    "Vous devez ajouter au moins une ligne de produit "
                    "avant de soumettre la demande."))
            rec.state = 'to_approve_shop'

    def action_validate_shop(self):
        """Responsable Boutique -> valide et soumet au Responsable Magasin."""
        for rec in self:
            for line in rec.line_ids:
                if not line.approved_qty:
                    line.approved_qty = line.requested_qty
            rec.write({
                'state': 'to_approve_warehouse',
                'date_shop_validation': fields.Datetime.now(),
            })

    def action_refuse_shop(self):
        for rec in self:
            rec.state = 'refused'

    def action_approve_warehouse(self):
        """Responsable Magasin -> approuve et déclenche le transfert."""
        for rec in self:
            if not rec.warehouse_id:
                raise UserError(_(
                    "Aucun magasin d'approvisionnement n'est défini pour "
                    "la boutique %s.") % rec.shop_id.name)
            picking = rec._create_stock_picking()
            rec.write({
                'state': 'approved',
                'picking_id': picking.id,
                'date_warehouse_validation': fields.Datetime.now(),
            })

    def action_refuse_warehouse(self):
        for rec in self:
            rec.state = 'refused'

    def action_reset_draft(self):
        for rec in self:
            rec.write({'state': 'draft', 'refusal_reason': False})

    def action_view_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.picking_id.id,
        }

    def _create_stock_picking(self):
        self.ensure_one()
        warehouse = self.warehouse_id
        picking_type = warehouse.int_type_id or self.env['stock.picking.type'].search([
            ('warehouse_id', '=', warehouse.id),
            ('code', '=', 'internal'),
        ], limit=1)
        if not picking_type:
            raise UserError(_(
                "Aucun type d'opération de transfert interne n'a été "
                "trouvé pour le magasin %s.") % warehouse.name)

        move_lines = []
        for line in self.line_ids:
            qty = line.approved_qty or line.requested_qty
            if qty <= 0:
                continue
            move_lines.append((0, 0, {
                'name': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': qty,
                'product_uom': line.uom_id.id,
                'location_id': warehouse.lot_stock_id.id,
                'location_dest_id': self.shop_id.location_id.id,
            }))

        if not move_lines:
            raise UserError(_(
                "Aucune quantité approuvée à transférer sur cette demande."))

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': warehouse.lot_stock_id.id,
            'location_dest_id': self.shop_id.location_id.id,
            'origin': self.name,
            'move_ids_without_package': move_lines,
        })
        picking.action_confirm()
        picking.action_assign()
        return picking
