# Format des Solutions MPVRP-CC

## Nomenclature des fichiers

Les fichiers de solution doivent suivre la nomenclature suivante :
```
Sol_MPVRP_{id_instance}_s{nb_stations}_d{nb_depots}_p{nb_produits}.dat
```

**Exemple :** `Sol_MPVRP_3_s3_d1_p2.dat` est la solution pour l'instance `MPVRP_3_s3_d1_p2.dat`

---

## Structure du fichier de solution

### Bloc 1 à N : Routes des véhicules

Chaque véhicule dispose de **deux²   lignes** :


#### Ligne 1 : Itinéraire avec quantités livrées et chargées
```
1: 1 - 1 [150] - 2 (51) - 3 (63) - 4 (18) - 1 [80] - 5 (93) - 6 (94) - 7 (45) - 8 (30) - 1
```

**Format :** `ID du véhicule: garage - dépôt [ quantité_chargée ] - station ( quantité_livrée ) - station ( quantité_livrée ) - dépôt [ quantité_chargée ] - station ( quantité_livrée ) - ... - garage`

**Structure logique :**
- Le véhicule **part d'un garage** (nœud sans parenthèse)
- Se rend à un **dépôt pour se charger** (nœud avec crochets pour la quantité chargée)
- Effectue une **mini-tournée de livraisons aux stations** (nœuds avec parenthèses pour les quantités livrées)
- Retourne au **dépôt pour se recharger** (optionnel, peut changer de dépôt ; quantité chargée entre crochets)
- Effectue une **nouvelle mini-tournée** avec possiblement un produit différent
- Retourne à un **garage** (nœud sans parenthèse)

**IDs des nœuds (sans accumulation, sans préfixe) :**

Les IDs gardent la plage de l'instance et sont écrits sans préfixe. Le type est inféré par convention :
- 1er et dernier nœud : garages
- nœud avec `[Qté]` : dépôt
- nœud avec `(Qté)` : station

**Exemple :** Pour une instance avec 2 garages, 4 dépôts et 16 stations :
- Garages : `1`, `2` (uniquement en première/dernière position)
- Dépôts : `1..4` (identifiés car suivis de crochets)
- Stations : `1..16` (identifiées car suivies de parenthèses)

**Quantité :** 
- Entre crochets `[Qté]` pour les dépôts : quantité chargée à ce nœud
- Entre parenthèses `(Qté)` pour les stations : quantité livrée à ce nœud
- 0 ou absent pour les garages

#### Ligne 2 : Produits et coûts cumulés
```
1: 3(0.0) - 3(0.0) - 3(0.0) - 3(0.0) - 3(0.0) - 2(14.4) - 2(14.4) - 2(14.4) - 2(14.4) - 1(39.4) - 1(39.4) - 1(39.4)
```

**Format :** `ID du véhicule: produit(coût_cumulé) - produit(coût_cumulé) - ...`

**Signification :**
- Le chiffre avant la parenthèse : numéro du produit transporté
- Le coût entre parenthèses : coût cumulé de changement de produit depuis le début de la route
- Le **changement de produit** se produit lors d'un passage au dépôt (nœud sans parenthèse)

**Exemple d'analyse :**
- Position 1-5 : Produit 3 à coût 0.0 (aucun changement)
- Position 6 : Au dépôt, changement de 3→2, coût ajouté = 14.4
- Positions 7-9 : Produit 2 à coût cumulé 14.4
- Position 10 : Au dépôt, changement de 2→1, coût ajouté = 25.0, coût cumulé = 39.4
- Positions 11-12 : Produit 1 à coût cumulé 39.4

#### Ligne 4 : Ligne vide (séparation entre véhicules)

---

## Bloc final : Métriques de la solution

Après les routes de tous les véhicules, le fichier contient 6 lignes de métriques :

```
2
0
0.0
401.86
Intel Core i7-10700K
0.245
```

### Ligne 1 : Nombre de véhicules utilisés
```
2
```
Nombre de véhicules ayant au moins une livraison

### Ligne 2 : Nombre de changements de produit
```
0
```
Nombre total de changements de produit dans la solution

### Ligne 3 : Coût total des transitions
```
0.0
```
Somme des coûts de changement de produit pour tous les véhicules

### Ligne 4 : Distance totale
```
401.86
```
Distance totale parcourue par la flotte (somme des distances euclidiennes)

### Ligne 5 : Processeur
```
Intel Core i7-10700K
```
Modèle du processeur sur lequel la solution a été générée

### Ligne 6 : Temps de résolution
```
0.245
```
Temps écoulé pour générer la solution (en secondes)

---

## Exemple complet

Pour l'instance `MPVRP_3_s3_d1_p2.dat` :
- 2 produits
- 1 dépôt
- 2 garages
- 3 stations
- 2 véhicules

**IDs des nœuds (sans accumulation, sans préfixe) :**
- Garages : `1`, `2`
- Dépôt : `1`
- Stations : `1`, `2`, `3`

**Exemple de fichier solution :**
```
1: 1 - 1 [1344] - 2 (1344) - 1
1: 0(0.0) - 0(0.0) - 0(0.0)

2: 1 - 1 [8947] - 1 (4278) - 2 (2350) - 3 (2319) - 1
2: 1(0.0) - 1(0.0) - 1(0.0) - 1(0.0) - 1(0.0)

2
0
0.0
401.86
Intel Core i7-10700K
0.245
```

**Analyse :**
- **Véhicule 1** : Garage `1` → Dépôt `1` [chargement 1344 de produit 0] → Station `2` (livraison 1344) → Garage `1`
  - Une seule mini-tournée, produit 0, pas de changement
  
- **Véhicule 2** : Garage `1` → Dépôt `1` [chargement 8947 de produit 1] → Station `1` (livraison 4278) → Station `2` (livraison 2350) → Station `3` (livraison 2319) → Garage `1`
  - Une seule mini-tournée, produit 1, pas de changement

---

## Compatibilité (ancien format)

Les anciens fichiers utilisaient une numérotation combinée par offsets (garages puis dépôts puis stations). Le solveur exporte
désormais en IDs typés; le vérificateur et la visualisation acceptent encore l'ancien format pour relire d'anciennes solutions.
  
- **Métriques** : 2 véhicules utilisés, 0 changement de produit, coût 0.0
