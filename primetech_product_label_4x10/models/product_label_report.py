from odoo import api, models


class ReportProductLabelCustom(models.AbstractModel):
    _name = "report.primetech_product_label_4x10.report_product_label_custom"
    _description = "Étiquettes produits PrimeTech"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        wizard = self.env["primetech.product.label.layout"].browse(data.get("wizard_id")).exists()
        wizard.ensure_one()
        layouts = {
            # format: (colonnes, lignes, hauteur imprimable en millimètres)
            # Une réserve verticale est volontairement conservée pour les
            # métriques internes de wkhtmltopdf. Sans elle, la dixième ligne
            # A4 est repoussée sur une seconde page malgré les marges du papier.
            "dymo": (1, 1, 88.0),
            "2x7xprice": (2, 7, 190.0),
            "4x7xprice": (4, 7, 270.0),
            "4x12": (4, 12, 270.0),
            "4x12xprice": (4, 12, 270.0),
            # Feuille A4 prédécoupée : 11 étiquettes de 25,45 mm de haut.
            # La réserve restante en bas de page évite tout débordement PDF.
            "4x11xprice": (4, 11, 280.0),
            "zpl": (1, 1, 130.0),
            "zplxprice": (1, 1, 130.0),
            "4x10xprice": (4, 10, 270.0),
        }
        columns, rows, page_height_mm = layouts[wizard.print_format]
        labels = [
            product
            for product in wizard.product_tmpl_ids
            for _index in range(wizard.quantity)
        ]
        page_size = columns * rows
        pages = []
        for start in range(0, len(labels), page_size):
            page = labels[start : start + page_size]
            page += [False] * (page_size - len(page))
            pages.append([page[index : index + columns] for index in range(0, page_size, columns)])
        prices = {}
        currencies = {}
        for product in wizard.product_tmpl_ids:
            if wizard.pricelist_id:
                prices[product.id] = wizard.pricelist_id._get_product_price(product, 1.0)
                currencies[product.id] = wizard.pricelist_id.currency_id
            else:
                prices[product.id] = product.list_price
                currencies[product.id] = product.currency_id
        return {
            "doc_ids": wizard.ids,
            "doc_model": wizard._name,
            "docs": wizard,
            "wizard": wizard,
            "pages": pages,
            "columns": columns,
            "rows": rows,
            "price_included": "xprice" in wizard.print_format,
            "prices": prices,
            "currencies": currencies,
            "page_height_mm": page_height_mm,
            # border-spacing ajoute un espace avant/après chaque ligne.
            "label_height_mm": page_height_mm / rows,
        }
