{
    "name": "PrimeTech Stock Alert by Location",
    "version": "18.0.1.0.0",
    "author": "PrimeTech",
    "website": "https://primetech.cm",
    "license": "LGPL-3",
    "category": "Inventory",

    "summary": "Stock alerts by location and lot",

    "description": """
PrimeTech Stock Alert

Features
---------
- Minimum stock per location
- Minimum stock per lot
- Quantity dashboard
- Editable thresholds
- Smart button
- Automatic alerts
""",

    "depends": [
        "stock",
    ],

    "data": [

        "security/ir.model.access.csv",

        "views/stock_location_alert_views.xml",
        "views/product_product_views.xml",
        "views/product_template_views.xml",
        "views/product_packaging_views.xml",

        "views/menus.xml",

        "data/ir_cron.xml",
    ],

    

    "installable": True,
    "application": False,
}