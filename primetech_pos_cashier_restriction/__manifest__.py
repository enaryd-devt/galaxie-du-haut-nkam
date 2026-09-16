{
    "name": "PrimeTech POS Cashier Restriction",
    "version": "18.0.1.5.0",
    "category": "Point of Sale",
    "summary": "Employee access levels for POS orders, printing and refunds",
    "description": """
PrimeTech POS Cashier Restriction
=================================

Configure cashier permissions directly on each Point of Sale.

Features
--------
* Three employee access levels per POS: restricted cashier, orders without refund, and refund manager.
* Restricted cashiers can sell and take payments but cannot view previous orders, print old receipts, or refund.
* Orders without refund cashiers can view and print orders but cannot refund.
* Refund managers keep full access.
* The POS loads the employee lists with its configuration and applies the selected cashier's permissions immediately.
* Employees not assigned to an access level keep full POS access.
* Employee access groups are mutually exclusive for each POS configuration.

How to use
----------
Open Point of Sale > Configuration > Settings > Cashier Security. Add each employee to one access level,
save the configuration, then reload the POS. The module requires the Multi-Employee POS feature (pos_hr).
""",
    "author": "PrimeTech Services",
    "license": "LGPL-3",
    "depends": [
        "base",
        "point_of_sale",
        "pos_hr",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/pos_config_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "primetech_pos_cashier_restriction/static/src/js/pos_order_restriction.js",
            "primetech_pos_cashier_restriction/static/src/js/pos_refund_restriction.js",
            "primetech_pos_cashier_restriction/static/src/xml/pos_restriction_templates.xml",
        ],
    },
    "installable": True,
    "application": False,
}
