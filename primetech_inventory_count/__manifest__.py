{
    "name": "PrimeTech Inventory Count",
    "version": "18.0.1.0.0",
    "category": "Inventory",
    "summary": "Feuilles de comptage par emplacement",
    "author": "PrimeTech Services",
    "license": "LGPL-3",
    "depends": [
        "stock",
        "product",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/inventory_count_menu.xml",
        "views/inventory_count_sheet_views.xml",
        "views/inventory_count_line_views.xml",
        "views/inventory_adjustment_preview_views.xml",
        "views/inventory_adjustment_log_views.xml",

    ],

    'assets': {
        'web.assets_backend': [

            'primetech_inventory_count/static/src/js/*.js',
            'primetech_inventory_count/static/src/components/*.js',
            'primetech_inventory_count/static/src/components/*.xml',
            'primetech_inventory_count/static/src/scss/*.scss',
        ],
    },
    "installable": True,
    "application": False,
}