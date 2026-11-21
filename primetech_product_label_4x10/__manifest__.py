{
    "name": "Étiquettes produits professionnelles",
    "summary": "Imprime des planches A4 d'étiquettes avec prix et codes-barres",
    # Keep the description in the manifest: the legacy repository README is
    # UTF-16 and must never be decoded by Odoo as the module description.
    "description": "Assistant français d'impression d'étiquettes produits professionnelles.",
    "version": "18.0.4.7.0",
    "category": "Sales/Products",
    "author": "PrimeTech",
    "license": "LGPL-3",
    "depends": ["product"],
    "data": [
        "security/ir.model.access.csv",
        "report/product_label_paperformat.xml",
        "report/product_label_templates.xml",
        "report/product_label_report.xml",
        "views/product_label_layout_views.xml",
        "views/product_template_views.xml",
    ],
    "installable": True,
    "application": False,
}
