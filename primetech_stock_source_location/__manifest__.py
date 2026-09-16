{
    'name': 'PrimeTech - Emplacement Source par Ligne',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Sélection et réservation d’un emplacement source par ligne de transfert',
    'description': """
PrimeTech - Emplacement Source par Ligne
========================================

Sécurisez et fiabilisez les prélèvements de stock ligne par ligne.

Chaque opération peut sélectionner un emplacement interne précis dans le
périmètre de son entrepôt. Le module suggère automatiquement le meilleur
emplacement selon la disponibilité, affiche le stock réellement disponible,
et utilise le choix dans la réservation ainsi que lors de la validation.

Les contrôles serveur protègent les environnements multi-entrepôts et
multi-sociétés, tout en préservant la traçabilité native d’Odoo.
""",
    'author': 'PrimeTech Services',
    'license': 'LGPL-3',
    'depends': ['stock'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
}
