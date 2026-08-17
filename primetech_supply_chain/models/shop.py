# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PrimetechShop(models.Model):
    _name = 'primetech.shop'
    _description = "Boutique"
    _order = 'name'

    name = fields.Char(string="Nom de la boutique", required=True)
    code = fields.Char(string="Code")
    active = fields.Boolean(default=True)

    company_id = fields.Many2one(
        'res.company', string="Société",
        default=lambda self: self.env.company, required=True)

    responsable_boutique_id = fields.Many2one(
        'res.users', string="Responsable Boutique", required=True,
        help="Utilisateur qui traite et valide les demandes de "
             "réapprovisionnement de cette boutique.")

    responsable_magasin_id = fields.Many2one(
        'res.users', string="Responsable Magasin", required=True,
        help="Utilisateur qui approuve les demandes et déclenche "
             "les transferts de stock depuis le magasin central.")

    rayonniste_ids = fields.Many2many(
        'res.users', string="Rayonnistes",
        help="Utilisateurs autorisés à créer des demandes de "
             "réapprovisionnement pour cette boutique.")

    warehouse_id = fields.Many2one(
        'stock.warehouse', string="Magasin d'approvisionnement",
        required=True,
        help="Entrepôt/magasin central depuis lequel le stock sera "
             "transféré vers cette boutique.")

    location_id = fields.Many2one(
        'stock.location', string="Emplacement de stock de la boutique",
        required=True, domain=[('usage', '=', 'internal')],
        help="Emplacement de destination du transfert, représentant "
             "le stock physique de la boutique.")

    address = fields.Text(string="Adresse")

    request_count = fields.Integer(compute='_compute_request_count')

    def _compute_request_count(self):
        grouped = self.env['primetech.replenishment.request']._read_group(
            [('shop_id', 'in', self.ids)], ['shop_id'], ['__count'])
        mapped = {shop.id: count for shop, count in grouped}
        for shop in self:
            shop.request_count = mapped.get(shop.id, 0)

    def action_view_requests(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'primetech_supply_chain.action_replenishment_request')
        action['domain'] = [('shop_id', '=', self.id)]
        action['context'] = {'default_shop_id': self.id}
        return action

    _sql_constraints = [
        ('code_uniq', 'unique(code, company_id)',
         "Le code de la boutique doit être unique par société."),
    ]
