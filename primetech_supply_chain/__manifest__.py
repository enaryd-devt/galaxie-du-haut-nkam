# -*- coding: utf-8 -*-
{
    'name': "Primetech Supply Chain",
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': "Réapprovisionnement des boutiques, transferts inter-magasins et inventaires",
    'description': """
Primetech Services - Supply Chain
===================================================================
Ce module couvre progressivement la chaîne logistique d'un réseau de
boutiques (supermarché), en commençant par le réapprovisionnement :

1. Le **Rayonniste** crée une demande de réapprovisionnement pour sa boutique.
2. Le **Responsable Boutique** traite la demande (ajuste les quantités,
   valide ou refuse) et la soumet au responsable des magasins.
3. Le **Responsable des Magasins** traite à son tour la demande, l'approuve
   et déclenche automatiquement le transfert de stock (bon de livraison /
   transfert interne) depuis le magasin central vers la boutique.

Prochaines briques prévues : ordres de transfert inter-magasins et
gestion des inventaires (feuilles de comptage et régularisations).

Développé pour Primetech Services.
    """,
    'author': "Primetech Services",
    'company': "Primetech Services",
    'website': "https://www.primetech-services.com",
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'stock', 'uom'],
    'data': [
        'security/security_groups.xml',
        'security/security_rules.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/shop_views.xml',
        'views/replenishment_request_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
