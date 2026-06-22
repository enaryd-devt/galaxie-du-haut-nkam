from odoo import models, fields, api
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

class InventoryCountSheet(models.Model):
    _name = "primetech.inventory.count.sheet"
    _description = "Feuille de comptage"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"
    _order = "id desc"

    name = fields.Char(
        string="Référence",
        required=True,
        default="Nouveau",
        tracking=True,
        readonly=True,
        copy=False,
    )

    date_count = fields.Date(
        string="Date de comptage",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )

    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Entrepôt",
        required=True,
        tracking=True,
    )

    location_id = fields.Many2one(
        "stock.location",
        string="Emplacement principal",
        required=True,
        tracking=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Utilisateur",
        default=lambda self: self.env.user,
        readonly=True,
    )

    export_mode = fields.Selection(
        [
            ("update", "Mettre à jour uniquement"),
            ("create", "Créer uniquement"),
            ("both", "Créer et mettre à jour"),
        ],
        string="Mode d'envoi",
        default="both",
        required=True,
        tracking=True,
    )

    state = fields.Selection(
        [
            ("draft", "Brouillon"),
            ("counting", "Comptage"),
            ("review", "Contrôle"),
            ("validated", "Validé"),
            ("exported", "Exporté"),
            ("done", "Appliqué"),
            ("cancel", "Annulé"),
        ],
        string="Statut",
        default="draft",
        tracking=True,
    )

    line_ids = fields.One2many(
        "primetech.inventory.count.line",
        "sheet_id",
        string="Lignes de comptage",
    )

    validation_date = fields.Datetime(
        string="Date validation",
        readonly=True,
        copy=False,
    )

    validated_by = fields.Many2one(
        "res.users",
        string="Validé par",
        readonly=True,
        copy=False,
    )

    line_count = fields.Integer(
        compute="_compute_stats",
        string="Nb lignes",
    )

    product_count = fields.Integer(
        compute="_compute_stats",
        string="Nb produits",
    )

    difference_count = fields.Integer(
        compute="_compute_dashboard",
        string="Écarts",
    )

    missing_count = fields.Integer(
        compute="_compute_dashboard",
        string="Manquants",
    )

    excess_count = fields.Integer(
        compute="_compute_dashboard",
        string="Surplus",
    )

    validated_line_count = fields.Integer(
        compute="_compute_dashboard",
        string="Lignes validées",
    )

    has_difference = fields.Boolean(
        compute="_compute_dashboard",
        string="Présence d'écarts",
    )

    adjustment_date = fields.Datetime(
        string="Date application",
        readonly=True,
    )

    applied_by = fields.Many2one(
        "res.users",
        string="Appliqué par",
        readonly=True,
    )

    applied_line_count = fields.Integer(
        compute="_compute_dashboard"
    )

    allowed_location_ids = fields.Many2many(
        "stock.location",
        compute="_compute_allowed_locations",
    )

    barcode_scan = fields.Char(
        string="Scanner produit"
    )


    record_id = fields.Integer(
        string="Record ID",
        compute="_compute_record_id",
        store=False,
    )

    is_locked = fields.Boolean(
        compute="_compute_is_locked"
    )

    @api.depends("state")
    def _compute_is_locked(self):

        for rec in self:

            rec.is_locked = rec.state in (
                "validated",
                "exported",
                "cancel",
            )

    def _compute_record_id(self):
        for rec in self:
            rec.record_id = rec.id

  
    def action_scan_barcode(self, barcode):

        self.ensure_one()

        _logger.warning(
            "SCAN FEUILLE=%s BARCODE=%s",
            self.id,
            barcode,
        )

        barcode = (barcode or "").strip()

        if not barcode:

            return {
                "success": False,
                "message": "Code-barres vide.",
            }

        product = self.env[
            "product.product"
        ].search(
            [
                ("barcode", "=", barcode)
            ],
            limit=1,
        )

        if not product:

            _logger.warning(
                "CODE BARRE INTROUVABLE : %s",
                barcode,
            )

            return {
                "success": False,
                "message": (
                    f"Le code-barres {barcode} n'existe pas."
                ),
            }

        line = self.env[
            "primetech.inventory.count.line"
        ].create({

            "sheet_id": self.id,

            "product_id": product.id,

            "count_location_id":
                self.location_id.id
                if self.location_id
                else False,

            "qty_counted": 1,

            "generated": False,

            "validated": False,

            "is_manual": True,
        })

        _logger.warning(
            "LIGNE AJOUTEE ID=%s PRODUIT=%s",
            line.id,
            product.display_name,
        )

        return {

            "success": True,

            "product_name":
                product.display_name,

            "line_id":
                line.id,

            "message":
                f"{product.display_name} ajouté.",
        }
    
    
    @api.onchange("warehouse_id")
    def _onchange_warehouse_id(self):

        for sheet in self:

            sheet.location_id = False

                # On vide les lignes uniquement
                # si l'utilisateur change réellement d'entrepôt

            if sheet.line_ids:
                    sheet.line_ids = [(5, 0, 0)]

    @api.depends("warehouse_id")
    def _compute_allowed_locations(self):

        Location = self.env["stock.location"]

        for rec in self:

            if rec.warehouse_id:

                rec.allowed_location_ids = Location.search([
                    (
                        "id",
                        "child_of",
                        rec.warehouse_id.view_location_id.id
                    )
                ])

            else:
                rec.allowed_location_ids = False

    @api.constrains("line_ids")
    def _check_location_before_lines(self):

        for rec in self:

            if rec.line_ids and not rec.location_id:

                raise ValidationError(
                    "Veuillez sélectionner un emplacement avant de saisir des lignes."
                )


    @api.depends("line_ids")
    def _compute_stats(self):

        for rec in self:

            rec.line_count = len(rec.line_ids)

            rec.product_count = len(
                rec.line_ids.mapped("product_id")
            )

    @api.depends(
        "line_ids.is_difference",
        "line_ids.difference_type",
        "line_ids.validated",
        "line_ids.adjustment_applied",
    )
    def _compute_dashboard(self):

        for rec in self:

            rec.difference_count = 0
            rec.missing_count = 0
            rec.excess_count = 0
            rec.validated_line_count = 0
            rec.applied_line_count = 0
            rec.has_difference = False

            rec.difference_count = len(
                rec.line_ids.filtered(
                    lambda l: l.is_difference
                )
            )

            rec.missing_count = len(
                rec.line_ids.filtered(
                    lambda l: l.difference_type == "missing"
                )
            )

            rec.excess_count = len(
                rec.line_ids.filtered(
                    lambda l: l.difference_type == "excess"
                )
            )

            rec.validated_line_count = len(
                rec.line_ids.filtered(
                    lambda l: l.validated
                )
            )

            rec.applied_line_count = len(
                rec.line_ids.filtered(
                    lambda l: l.adjustment_applied
                )
            )

            rec.has_difference = (
                rec.difference_count > 0
            )

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            if vals.get("name", "Nouveau") == "Nouveau":

                vals["name"] = self.env[
                    "ir.sequence"
                ].next_by_code(
                    "primetech.inventory.count.sheet"
                )

        return super().create(vals_list)
    def action_generate_lines(self):

        self.ensure_one()

        if not self.location_id:
            raise UserError(
                "Veuillez sélectionner un emplacement principal."
            )

        existing_keys = set()

        for line in self.line_ids:

            existing_keys.add((
                line.product_id.id,
                line.lot_id.id if line.lot_id else False,
                line.system_location_id.id
                if line.system_location_id
                else False,
            ))

        quants = self.env["stock.quant"].search([
            ("location_id", "child_of", self.location_id.id),
            ("quantity", ">", 0),
        ])

        new_lines = []

        for quant in quants:

            key = (
                quant.product_id.id,
                quant.lot_id.id if quant.lot_id else False,
                quant.location_id.id,
            )

            if key in existing_keys:
                continue

            expiration = False

            if (
                quant.lot_id
                and hasattr(
                    quant.lot_id,
                    "expiration_date"
                )
            ):
                expiration = quant.lot_id.expiration_date

            new_lines.append((0, 0, {

                "product_id":
                    quant.product_id.id,

                "system_location_id":
                    quant.location_id.id,

                "count_location_id":
                    quant.location_id.id,

                "lot_id":
                    quant.lot_id.id,

                "expiration_date":
                    expiration,

                "qty_system":
                    quant.quantity,

                "qty_counted":
                    quant.quantity,

                "generated":
                    True,

            }))

        if new_lines:

            self.write({
                "line_ids": new_lines
            })

        if self.state == "draft":

            self.state = "counting"

        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }
    def action_confirm(self):

        for rec in self:

            if not rec.line_ids:

                raise UserError(
                    "Aucune ligne de comptage."
                )

            rec.state = "review"

        return True

    def action_review(self):

        if not self.line_ids:
            raise UserError(
                "Aucune ligne de comptage."
            )

        self.state = "review"

        return True

    def action_validate(self):

        if not self.line_ids:
            raise UserError(
                "Aucune ligne de comptage."
            )

        self.write({
            "state": "validated",
            "validation_date": fields.Datetime.now(),
            "validated_by": self.env.user.id,
        })

        return True



    def action_export_to_odoo_inventory(self):

    
        self.ensure_one()

        if self.state == "exported":
            raise UserError(
                "Cette feuille a déjà été exportée."
            )

        if not self.line_ids:
            raise UserError(
                "Aucune ligne à exporter."
            )

        Log = self.env[
            "primetech.inventory.adjustment.log"
        ]

        grouped_lines = {}

        # =====================================
        # CONSOLIDATION DES LIGNES
        # =====================================

        for line in self.line_ids:

            key = (

                line.product_id.id,

                line.barcode or "",

                line.lot_id.id if line.lot_id else False,

                line.expiration_date or False,

                line.count_location_id.id if line.count_location_id else False,
            )

            if key not in grouped_lines:

                grouped_lines[key] = {

                    "product_id":
                        line.product_id,

                    "lot_id":
                        line.lot_id,

                    "expiration_date":
                        line.expiration_date,

                    "location_id":
                        line.count_location_id,

                    "qty_counted":
                        0.0,

                    "qty_system":
                        0.0,

                    "lines":
                        self.env[
                            "primetech.inventory.count.line"
                        ],
                }

            grouped_lines[key]["qty_counted"] += (
                line.qty_counted
            )

            grouped_lines[key]["qty_system"] += (
                line.qty_system
            )

            grouped_lines[key]["lines"] |= line

        exported_count = 0

        # =====================================
        # EXPORT CONSOLIDÉ
        # =====================================

        for data in grouped_lines.values():

            quant = self.env["stock.quant"].search(
                [
                    (
                        "product_id",
                        "=",
                        data["product_id"].id
                    ),
                    (
                        "location_id",
                        "=",
                        data["location_id"].id
                    ),
                    (
                        "lot_id",
                        "=",
                        data["lot_id"].id
                        if data["lot_id"]
                        else False
                    ),
                    (
                        "company_id",
                        "=",
                        self.env.company.id
                    ),
                ],
                limit=1,
            )

            if not quant:

                quant = self.env[
                    "stock.quant"
                ].create({

                    "product_id":
                        data["product_id"].id,

                    "location_id":
                        data["location_id"].id,

                    "lot_id":
                        data["lot_id"].id
                        if data["lot_id"]
                        else False,

                    "company_id":
                        self.env.company.id,
                })

            quant.write({

                "inventory_quantity":
                    data["qty_counted"],

                "inventory_quantity_set":
                    True,
            })

            Log.create({

                "sheet_id":
                    self.id,

                "product_id":
                    data["product_id"].id,

                "lot_id":
                    data["lot_id"].id
                    if data["lot_id"]
                    else False,

                "expiration_date":
                    data["expiration_date"],

                "warehouse_id":
                    self.warehouse_id.id,

                "location_id":
                    data["location_id"].id,

                "qty_system":
                    data["qty_system"],

                "qty_counted":
                    data["qty_counted"],

                "before_qty":
                    data["qty_system"],

                "after_qty":
                    data["qty_counted"],

                "difference":
                    data["qty_counted"]
                    - data["qty_system"],

                "difference_type":
                    (
                        "excess"
                        if data["qty_counted"]
                        > data["qty_system"]
                        else
                        "missing"
                        if data["qty_counted"]
                        < data["qty_system"]
                        else
                        "equal"
                    ),

                "counted_by":
                    self.env.user.id,

                "adjustment_date":
                    fields.Datetime.now(),
            })

            data["lines"].write({

                "adjustment_applied": True,

                "validated": True,
            })

            exported_count += 1

        self.write({

            "state": "exported",

            "adjustment_date":
                fields.Datetime.now(),

            "applied_by":
                self.env.user.id,
        })

        return {

            "type":
                "ir.actions.client",

            "tag":
                "display_notification",
            
            "tag": "reload",

            "params": {

                "title":
                    "Export terminé",

                "message":
                    (
                        f"{exported_count} ligne(s) "
                        f"consolidée(s) exportée(s) "
                        f"vers l'inventaire Odoo."
                    ),

                "type":
                    "success",

                "sticky":
                    False,
            },
        }


    def action_cancel(self):

        self.write({
            "state": "cancel"
        })

        return True

    def action_view_lines(self):
        return True

    def action_view_products(self):
        return True

    def action_view_differences(self):
        return True

    def action_view_missing(self):
        return True

    def action_view_excess(self):
        return True
    
    def action_add_product_wizard(self):
        return True

    def unlink(self):

        for rec in self:

            if rec.state in (
                "validated",
                "Sent",
            ):
                raise UserError(
                    "Impossible de supprimer une feuille validée."
                )

        return super().unlink()
    
    def action_preview_adjustments(self):

        self.ensure_one()

        Preview = self.env[
            "primetech.inventory.adjustment.preview"
        ]

        # Nettoyage ancienne prévisualisation
        Preview.search([
            ("sheet_id", "=", self.id)
        ]).unlink()

        # Génération
        for line in self.line_ids:

            Preview.create({

                "sheet_id":
                    self.id,

                "line_id":
                    line.id,

                "product_id":
                    line.product_id.id,

                "lot_id":
                    line.lot_id.id or False,

                "system_location_id":
                    line.system_location_id.id or False,

                "count_location_id":
                    line.count_location_id.id or False,

                "qty_system":
                    line.qty_system,

                "qty_counted":
                    line.qty_counted,

                "difference":
                    line.difference,

                "difference_type":
                    line.difference_type,

                "location_difference":
                    line.location_difference,
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Prévisualisation des ajustements",
            "res_model":
                "primetech.inventory.adjustment.preview",
            "view_mode": "list",
            "target": "new",
            "domain": [
                ("sheet_id", "=", self.id)
            ],
        }
    

    def action_reset_to_draft(self):

        self.ensure_one()

        if not self.env.user.has_group(
            "primetech_inventory_count.group_inventory_manager"
        ):
            raise UserError(
                "Vous n'avez pas les droits nécessaires."
            )

        self.write({

            "state": "draft",

            "validated_by": False,

            "validation_date": False,

            "applied_by": False,

            "adjustment_date": False,

        })

        return True
    
    def write(self, vals):

        protected_fields = {
            "warehouse_id",
            "location_id",
            "line_ids",
            "export_mode",
        }

        for rec in self:

            if rec.state in (
                "validated",
                "exported",
                "cancel",
            ):

                if protected_fields.intersection(vals.keys()):

                    raise UserError(
                        "Cette feuille est verrouillée."
                    )

        return super().write(vals)