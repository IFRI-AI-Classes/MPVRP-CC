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

Chaque véhicule dispose de **deux lignes** :

#### Ligne 1 : Itinéraire avec quantités livrées
```
1 - 3 - 8 ( 51 ) - 9 ( 63 ) - 10 ( 18 ) - 3 - 11 ( 93 ) - 12 ( 94 ) - 2 - 19 ( 45 ) - 20 ( 30 ) - 1
```

**Format :** `garage - dépôt - station ( quantité ) - station ( quantité ) - dépôt - station ( quantité ) - ... - garage`

**Structure logique :**
- Le véhicule **part d'un garage** (nœud sans parenthèse)
- Se rend à un **dépôt pour se charger** (nœud sans parenthèse)
- Effectue une **mini-tournée de livraisons aux stations** (nœuds avec parenthèses)
- Retourne au **dépôt pour se recharger** (optionnel, peut changer de dépôt)
- Effectue une **nouvelle mini-tournée** avec possiblement un produit différent
- Retourne à un **garage** (nœud sans parenthèse)

**Codification des nœuds :**
- Nœuds 1 à NbGarages : Garages
- Nœuds NbGarages+1 à NbGarages+NbDépôts : Dépôts
- Nœuds NbGarages+NbDépôts+1 à NbGarages+NbDépôts+NbStations : Stations

**Exemple :** Pour une instance avec 2 garages, 4 dépôts et 16 stations :
- Garages : 1, 2
- Dépôts : 3, 4, 5, 6
- Stations : 7, 8, 9, ..., 22

**Quantité :** La quantité entre parenthèses indique la quantité livrée à ce nœud 
- 0 ou absent pour les garages et dépôts
- > 0 pour les stations uniquement

#### Ligne 2 : Produits et coûts cumulés
```
3(0.0) - 3(0.0) - 3(0.0) - 3(0.0) - 3(0.0) - 2(14.4) - 2(14.4) - 2(14.4) - 2(14.4) - 1(39.4) - 1(39.4) - 1(39.4)
```

**Format :** `produit(coût_cumulé) - produit(coût_cumulé) - ...`

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

#### Ligne 3 : Ligne vide (séparation entre véhicules)

---

## Bloc final : Métriques de la solution

Après les routes de tous les véhicules, le fichier contient 6 lignes de métriques :

```
2
7
55.66
1385.07
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
7
```
Nombre total de changements de produit dans la solution

### Ligne 3 : Coût total des transitions
```
55.66
```
Somme des coûts de changement de produit pour tous les véhicules

### Ligne 4 : Distance totale
```
1385.07
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

**Codification des nœuds :**
- Garages : 1, 2
- Dépôt : 3
- Stations : 4, 5, 6

**Exemple de fichier solution :**
```
1 - 3 - 4 ( 100 ) - 5 ( 50 ) - 3 - 6 ( 80 ) - 1
1(0.0) - 1(0.0) - 1(0.0) - 1(0.0) - 2(25.3) - 2(25.3) - 2(25.3)

2 - 3 - 4 ( 75 ) - 2
2(0.0) - 2(0.0) - 2(0.0) - 2(0.0)

2
1
25.30
245.32
Intel Core i7-10700K
0.152
```

**Analyse :**
- **Véhicule 1** : Garage 1 → Dépôt 3 → Stations 4,5 → Dépôt 3 → Station 6 → Garage 1
  - Mini-tournée 1 : Produit 1 (stations 4,5)
  - Changement au dépôt 3 : 1→2 (coût 25.3)
  - Mini-tournée 2 : Produit 2 (station 6)
  
- **Véhicule 2** : Garage 2 → Dépôt 3 → Station 4 → Garage 2
  - Une seule mini-tournée, pas de changement
  
- **Métriques** : 2 véhicules utilisés, 1 changement de produit, coût 25.30
