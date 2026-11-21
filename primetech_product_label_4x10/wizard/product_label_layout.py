from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PrimetechProductLabelLayout(models.TransientModel):
    """Assistant indépendant de mise en page des étiquettes PrimeTech."""

    _name = "primetech.product.label.layout"
    _description = "Mise en page des étiquettes produits PrimeTech"

    quantity = fields.Integer(string="Quantité par produit", default=1, required=True)
    print_format = fields.Selection(
        [
            ("dymo", "Dymo"),
            ("2x7xprice", "2 x 7 avec le prix"),
            ("4x7xprice", "4 x 7 avec le prix"),
            ("4x12", "4 x 12"),
            ("4x12xprice", "4 x 12 avec le prix"),
            ("4x11xprice", "4 x 11 avec le prix"),
            ("zpl", "Étiquettes ZPL"),
            ("zplxprice", "Étiquettes ZPL avec prix"),
            ("4x10xprice", "4 x 10 avec le prix"),
        ],
        string="Format d'impression",
        default="4x11xprice",
        required=True,
    )
    product_tmpl_ids = fields.Many2many(
        "product.template",
        string="Produits",
        required=True,
    )
    pricelist_id = fields.Many2one("product.pricelist", string="Liste de prix")
    extra_html = fields.Html(string="Contenu supplémentaire")
    format_filename = fields.Char(
        string="Nom du fichier",
        compute="_compute_format_filename",
    )

    @api.depends("print_format")
    def _compute_format_filename(self):
        labels = dict(self._fields["print_format"].selection)
        for wizard in self:
            wizard.format_filename = labels.get(wizard.print_format, "Étiquettes produits")

    def action_print(self):
        self.ensure_one()
        if self.quantity <= 0:
            raise UserError(_("La quantité d'étiquettes doit être supérieure à zéro."))
        if not self.product_tmpl_ids:
            raise UserError(_("Sélectionnez au moins un produit."))
        page_formats = {
            "dymo": "A7",
            "2x7xprice": "A5",
            "4x7xprice": "A4",
            "4x12": "A4",
            "4x12xprice": "A4",
            "4x11xprice": "A4",
            "zpl": "A6",
            "zplxprice": "A6",
            "4x10xprice": "A4",
        }
        report = self.env["ir.actions.report"].search(
            [
                ("report_name", "=", "primetech_product_label_4x10.report_product_label_custom"),
                ("paperformat_id.format", "=", page_formats[self.print_format]),
            ],
            limit=1,
        )
        if not report:
            raise UserError(_("Le rapport PDF d'étiquettes PrimeTech n'est pas installé."))
        return report.report_action(self, data={"wizard_id": self.id})
