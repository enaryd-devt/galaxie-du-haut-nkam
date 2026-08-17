# Primetech Supply Chain

Module Odoo 18 développé pour **Primetech Services**.

Ce module a vocation à couvrir progressivement toute la chaîne logistique
du réseau de boutiques : il démarre avec le **réapprovisionnement**, et
intégrera ensuite les **transferts inter-magasins** et la **gestion des
inventaires** (feuilles de comptage et régularisations).

## Objectif (brique actuelle : réapprovisionnement)
Gérer le circuit de réapprovisionnement d'un réseau de boutiques (supermarché) :

1. **Rayonniste** : crée une demande de réapprovisionnement pour sa boutique
   (liste de produits + quantités souhaitées), puis la soumet.
2. **Responsable Boutique** : traite la demande (ajuste les quantités
   approuvées si besoin), la valide et la transmet au responsable des magasins,
   ou la refuse.
3. **Responsable Magasin** : traite à son tour la demande, l'approuve — ce qui
   déclenche automatiquement un **transfert de stock Odoo** (stock.picking)
   depuis le magasin central vers l'emplacement de stock de la boutique — ou
   la refuse.

## Installation
1. Copier le dossier `primetech_supply_chain` dans votre dossier
   `addons` (ou le monter dans le conteneur Odoo).
2. Mettre à jour la liste des applications (mode développeur activé).
3. Installer le module « Primetech Supply Chain ».

## Configuration après installation
1. Aller dans **Réapprovisionnement > Configuration > Boutiques**.
2. Créer une boutique :
   - Renseigner le **Responsable Boutique** et le **Responsable Magasin**.
   - Renseigner les **Rayonnistes** autorisés.
   - Choisir le **Magasin d'approvisionnement** (stock.warehouse existant).
   - Choisir l'**Emplacement de stock de la boutique** (stock.location interne,
     à créer au préalable si besoin dans Inventaire > Configuration > Emplacements).
3. Attribuer les droits aux utilisateurs concernés dans
   **Réglages > Utilisateurs**, catégorie « Primetech - Réapprovisionnement » :
   - Rayonniste
   - Responsable Boutique
   - Responsable Magasin

## Utilisation
- Menu **Réapprovisionnement > Demandes**.
- Le rayonniste crée une demande en brouillon, ajoute des lignes de produits
  et clique sur **Soumettre à la boutique**.
- Le responsable boutique ajuste si besoin les quantités approuvées et clique
  sur **Valider et transmettre au magasin**, ou **Refuser**.
- Le responsable magasin clique sur **Approuver et lancer le transfert** :
  un transfert de stock est créé, confirmé et réservé automatiquement.
  Il peut être consulté via le bouton statistique « Transfert » sur la demande.

## Modèles techniques
- `primetech.shop` : Boutique (responsables, magasin lié, emplacement).
- `primetech.replenishment.request` : Demande de réapprovisionnement (workflow).
- `primetech.replenishment.line` : Lignes de produits demandés.

## Dépendances
`base`, `mail`, `stock`, `uom`
