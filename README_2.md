# MPVRP-CC / MPVRP-CRP (core/model)

Ce module contient le solveur et le vérificateur du **Multi-Product Vehicle Routing Problem** (multi-dépôts, multi-produits) avec **coût de changement de produit**. L’implémentation principale est en Python avec PuLP (CBC par défaut).

## Entrypoints

- Solveur (modèle par segments) : `core/model/mpvrp_solver.py`
- Vérificateur : `core/model/mpvrp_verify.py`
- Scoring / notation : `core/model/mpvrp_score.py`

Les fichiers d’instances sont dans `data/instances/` et les fichiers de solutions exportées dans `data/solutions/`.

## Format des instances (.dat)

La première ligne non commentée contient 5 entiers dans l’ordre suivant :

`NbProduits  NbDepots  NbGarages  NbStations  NbVehicules`

Puis :

1) matrice des coûts de changement (NbProduits lignes, NbProduits colonnes)
2) véhicules (NbVehicules lignes) : `ID  Capacité  GarageOrigine  ProduitInitial`
3) dépôts (NbDepots lignes) : `ID  X  Y  Stock_P1 ... Stock_Pp`
4) garages (NbGarages lignes) : `ID  X  Y`
5) stations (NbStations lignes) : `ID  X  Y  Demande_P1 ... Demande_Pp`

## Format des solutions (.dat)

Le solveur exporte des solutions au format texte à 2 lignes par véhicule, puis 6 lignes de métriques.

### IDs des nœuds (sans accumulation, sans préfixe)

Les IDs écrits dans le fichier solution sont des **entiers**, dans la même plage que dans l'instance (pas d'accumulation).
Le type est inféré par convention :

- 1er et dernier nœud de la route : garages
- nœud avec crochets `[q]` : dépôt
- nœud avec parenthèses `(q)` : station

Exemple : `2 - 1 [150] - 5 (93) - 2`.

Compatibilité : le vérificateur et la visualisation acceptent encore l'ancien format numérique par offsets (garages puis dépôts puis stations).

## Exécution

Depuis la racine du projet :

- Solveur : `python core/model/mpvrp_solver.py`
- Vérification d’une solution : `python core/model/mpvrp_verify.py`
- Score d’une solution : `python core/model/mpvrp_score.py`

Le script de scoring vérifie d’abord la validité de la solution, puis calcule un score (sur 100) basé sur l’utilisation de la flotte, la qualité du routage et la gestion des produits.

## Visualisation

La visualisation lit :

- une instance `.dat` (pour les coordonnées)
- une solution `.dat` (pour les arcs)

Fichier : `app/templates/visualisation.html`
