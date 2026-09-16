# PrimeTech POS Cashier Restriction

## Objectif

Ce module Odoo 18 Community sépare les opérations POS courantes des fonctions sensibles. Un caissier restreint peut vendre, encaisser et imprimer le ticket courant, mais ne peut pas accéder à l'historique, rechercher un ancien ticket, réimprimer une ancienne commande ou créer un remboursement.

## Installation

1. Copier le module dans le chemin addons de l'instance.
2. Mettre à jour la liste des applications.
3. Installer `PrimeTech POS Cashier Restriction`.
4. Redémarrer le service Odoo si les assets POS ne sont pas encore recompilés.

## Configuration

Dans Point de Vente, ouvrir la configuration du POS puis la section `Sécurité des caissiers`.

## Niveaux d'accès par caisse

- `Caissiers restreints` : vente et encaissement uniquement. Les commandes, anciennes impressions et remboursements sont bloqués.
- `Commandes sans remboursement` : vente, consultation et impression des commandes autorisées ; remboursement bloqué.
- `Responsables / remboursement` : vente, commandes, impressions et remboursements autorisés.

Les listes sont propres à chaque caisse. Le POS les charge au démarrage et applique le niveau de l'employé actuellement connecté. Un employé absent de ces trois listes conserve tous les droits POS.

## Sécurité

Le module combine trois niveaux de protection :

- OWL POS : masquage réel du menu `Orders`, du bouton `Refund` et blocage de la navigation directe.
- RPC/ORM : contrôle de `sync_from_ui`, `refund`, `search_paid_order_ids`, `create` et `write`.
- Record rules : limitation backend des commandes, lignes et paiements visibles par les caissiers restreints.

Les règles multi-société natives d'Odoo restent actives. Le module n'élargit jamais les droits inter-sociétés.

## Employés POS

Le module requiert `pos_hr`. Plusieurs employés peuvent utiliser la même caisse : le droit est recalculé dans le navigateur à chaque changement de caissier, depuis la configuration de cette caisse.

## Audit

Les tentatives serveur interdites sont journalisées et enregistrées dans `pos.restriction.audit` avec l'utilisateur, l'action, la commande, la session, la date et l'ID technique de l'employé si disponible.

## Limitations

- Les anciens groupes utilisateur du module sont neutralisés à la mise à jour ; ils ne définissent plus les droits POS.
- Les captures d'écran doivent être ajoutées après validation fonctionnelle sur l'environnement client.

## Dépannage

- Si le POS démarre sans les patches JS, vider les assets puis redémarrer Odoo.
- Si `point_of_sale` est introuvable, vérifier que le chemin addons standard Odoo est chargé par l'instance.
- Vérifier qu'un employé ne figure que dans un seul niveau de la configuration POS.
