# -*- coding: utf-8 -*-

{
    "name": "PrimeTech Association Management",
    "summary": "Association Management for Odoo 18 Community",
    "version": "18.0.1.0.0",
    "category": "Services",
    "author": "PrimeTech Services",
    "website": "https://www.primetechafrik.com",
    "license": "LGPL-3",

    "description": """
PrimeTech Association Management

Version de développement (Debug)

Fonctionnalités en cours de développement :
- Gestion des membres
- Cotisations
- Paiements
- Réunions
- Présences
- Dons
- Dépenses
- Tableau de bord
""",

    "depends": [
        "base",
        "mail",
        "contacts",
        "web",
    ],

    "data": [

        # =====================================================
        # SECURITY
        # =====================================================
        "security/association_security.xml",
        "security/ir.model.access.csv",

        # =====================================================
        # DATA
        # =====================================================
        "data/association_sequence.xml",

        # Les fichiers suivants seront réactivés progressivement
        # "data/member_category_data.xml",
        # "data/member_function_data.xml",
        # "data/mail_template.xml",
        # "data/association_cron.xml",

        # =====================================================
        # VIEWS
        # =====================================================

        # Aucune vue pour l'instant.
        # Nous les ajouterons une par une afin d'identifier
        # immédiatement le fichier qui pose problème.
    ],

    "demo": [],

    "images": [
        "static/description/banner.png",
    ],

    "installable": True,
    "application": True,
    "auto_install": False,
}