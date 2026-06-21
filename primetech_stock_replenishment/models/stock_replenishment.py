from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockReplenishment(models.Model):
    _name = "pt.stock.replenishment"
    _description = "Bon de Réapprovisionnement"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
    ]
    _order = "id desc"

    name = fields.Char(
        string="Référence",
        copy=False,
        readonly=True,
        default=lambda self: _("Nouveau"),
    )

    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Société",
        required=True,
        default=lambda self: self.env.company,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Préparé par",
        required=True,
        default=lambda self: self.env.user,
    )

    notes = fields.Text(
        string="Observations"
    )

    state = fields.Selection(
        [
            ("draft", "Brouillon"),
            ("approved", "Approuvé"),
            ("rfq", "RFQ Créée"),
            ("done", "Traité"),
            ("cancel", "Annulé"),
        ],
        default="draft",
        tracking=True,
    )

    line_ids = fields.One2many(
        "pt.stock.replenishment.line",
        "replenishment_id",
        string="Articles",
    )

    purchase_order_ids = fields.Many2many(
        "purchase.order",
        string="Demandes de Prix",
        readonly=True,
    )

    article_count = fields.Integer(
        compute="_compute_totals",
        store=True,
    )

    total_qty = fields.Float(
        compute="_compute_totals",
        store=True,
    )

    rfq_count = fields.Integer(
        compute="_compute_rfq_count"
    )

    @api.depends("line_ids.qty_to_order")
    def _compute_totals(self):

        for rec in self:

            rec.article_count = len(
                rec.line_ids
            )

            rec.total_qty = sum(
                rec.line_ids.mapped(
                    "qty_to_order"
                )
            )

    def _compute_rfq_count(self):

        for rec in self:

            rec.rfq_count = len(
                rec.purchase_order_ids
            )

    @api.model
    def create(self, vals):

        if not vals.get("name") or vals.get("name") == _("Nouveau"):

            vals["name"] = self.env[
                "ir.sequence"
            ].next_by_code(
                "pt.stock.replenishment"
            ) or _("Nouveau")

        return super().create(vals)
    

    def action_generate_products(self):

        self.ensure_one()

        self.line_ids.unlink()

        products = self.env[
            "product.product"
        ].search([])

        lines = []

        for product in products:

            if product.qty_available <= 0:

                lines.append((0, 0, {

                    "product_id":
                        product.id,

                    "qty_available":
                        product.qty_available,

                    "alert_quantity":
                        0,

                    "optimal_quantity":
                        0,

                    "qty_to_order":
                        1,

                }))

        self.write({
            "line_ids": lines
        })

        return True
    
    def action_approve(self):

        self.state = "approved"

    def action_cancel(self):

        self.state = "cancel"

    def action_reset_draft(self):

        self.state = "draft"

    def action_view_rfqs(self):

        self.ensure_one()

        return {

            "type":
                "ir.actions.act_window",

            "name":
                _("Demandes de Prix"),

            "res_model":
                "purchase.order",

            "view_mode":
                "list,form",

            "domain":
                [
                    (
                        "id",
                        "in",
                        self.purchase_order_ids.ids
                    )
                ],
        }

    def action_create_rfq(self):

        self.ensure_one()

        lines = self.line_ids.filtered(
            lambda l:
            l.selected
            and
            l.qty_to_order > 0
        )

        if not lines:

            raise UserError(
                _("Aucun article sélectionné.")
            )

        supplier = self.env.ref(
            "primetech_stock_replenishment.partner_supplier_to_define"
        )

        po = self.env[
            "purchase.order"
        ].create({

            "partner_id":
                supplier.id,

            "origin":
                self.name,

            "notes":
                """
        RFQ générée automatiquement depuis un Bon de Réapprovisionnement.

        IMPORTANT :
        - Remplacer 'FOURNISSEUR A DEFINIR' par le fournisseur réel.
        - Vérifier les quantités.
        - Vérifier les prix avant validation.
                """,

        })

        for line in lines:

            self.env[
                "purchase.order.line"
            ].create({

                "order_id":
                    po.id,

                "product_id":
                    line.product_id.id,

                "name":
                    line.product_id.display_name,

                "product_qty":
                    line.qty_to_order,

                "product_uom":
                    line.product_id.uom_po_id.id,

                "price_unit":
                    0.0,

                "date_planned":
                    fields.Datetime.now(),

            })

        self.write({

            "purchase_order_ids": [
                (4, po.id)
            ],

            "state": "rfq",

        })

        return {

            "type":
                "ir.actions.act_window",

            "res_model":
                "purchase.order",

            "res_id":
                po.id,

            "view_mode":
                "form",

        }