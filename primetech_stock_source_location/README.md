# PrimeTech - Emplacement Source par Ligne

## Objectif

Ce module permet de sélectionner l'emplacement interne de prélèvement pour chaque ligne d'un bon de livraison ou transfert interne. Le choix ne se limite pas à l'affichage : il pilote la réservation et les lignes de mouvement réellement validées.

## Installation

1. Placez le module dans un chemin `addons` d'Odoo 18 Community.
2. Mettez à jour la liste des applications.
3. Installez **PrimeTech - Emplacement Source par Ligne**.

## Fonctionnement

Dans l'onglet **Opérations** d'un transfert dont la source est interne, les colonnes **Disponible** et **Emplacement source** sont affichées sur chaque ligne. Les emplacements proposés couvrent tous les emplacements internes du même entrepôt, y compris leurs sous-emplacements, compatibles avec la société du transfert. Ainsi, pour une source d'en-tête `MAG1/A`, les lignes peuvent sélectionner `MAG1/A`, `MAG1/B`, `MAG1/C`, `MAG1/A/1A001` ou `MAG1/B/1B001`, sans jamais proposer un emplacement de `MAG2`.

Lorsqu'un produit est choisi, le module recherche les quantités disponibles par emplacement. Il privilégie un emplacement pouvant couvrir toute la demande puis, à défaut, celui qui a la meilleure disponibilité. Sans disponibilité, l'emplacement source par défaut de l'opération est retenu.

La disponibilité est celle du produit dans l'emplacement choisi, et non le stock global.

## Restrictions multi-entrepôts et multi-sociétés

Un transfert ne peut sélectionner que les emplacements internes de son entrepôt. Les emplacements d'un autre entrepôt ou d'une société incompatible sont exclus de la liste et refusés par une validation serveur.

## Réservation et validation

Le choix est synchronisé avec le mouvement stock natif. La réservation recherche les quants uniquement dans l'emplacement sélectionné et les lignes de mouvement utilisent ce même emplacement. À la validation, le stock est donc réellement décrémenté dans l'emplacement choisi, en conservant le fonctionnement natif des lots, numéros de série, colis et traçabilité.
