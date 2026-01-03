## Description de la Structure du Fichier d’Instance MPVRP-CC

<!-- TOC -->
  * [Description de la Structure du Fichier d’Instance MPVRP-CC](#description-de-la-structure-du-fichier-dinstance-mpvrp-cc)
  * [1 Introduction](#1-introduction)
  * [2 Nomenclature du Fichier](#2-nomenclature-du-fichier)
  * [3 Structure du Fichier](#3-structure-du-fichier)
    * [3.1 Détail de Chaque Section](#31-détail-de-chaque-section)
      * [3.1.1 Ligne 1 : Paramètres Globaux](#311-ligne-1--paramètres-globaux)
      * [3.1.2 Lignes 2 à (1+NbProduits) : Matrice de Coûts de Transition](#312-lignes-2-à-1nbproduits--matrice-de-coûts-de-transition)
      * [3.1.3 Véhicules](#313-véhicules)
      * [3.1.4 Dépôts](#314-dépôts)
      * [3.1.5 Garages](#315-garages)
      * [3.1.6 Stations](#316-stations)
  * [4 Exemple Complet](#4-exemple-complet)
<!-- TOC -->

## 1 Introduction

Le fichier d’instance pour le Multi-Product Vehicle Routing Problem with Changeover Cost
(MPVRP-CC) utilise un format texte compact et lisible appelé format .dat. Ce format est conçu pour
être facile à parser en Python tout en restant compréhensible par un humain.

## 2 Nomenclature du Fichier

Le nom du fichier suit le format suivant :

```text
MPVRP_A_sB_dC_pD.dat
```

— A : Identifiant de l’instance (ex : 01, 02, etc.)
— B : Nombre de stations (clients à livrer)
— C : Nombre de dépôts (points de chargement)
— D : Nombre de produits
Exemple : MPVRP_01_s10_d2_p3.dat représente une instance 01 avec 10 stations, 2 dépôts et 3 produits.

## 3 Structure du Fichier

Le fichier .dat est organisé en sections consécutives, chaque section étant un tableau NumPy exporté séparé
par des tabulations. Voici la structure générale :

```text
1 NbVehicules NbDepots NbGarages NbStations NbProduits
2
3 Cost_P1 ->P1 Cost_P1 ->P2 ... Cost_P1 ->Pp
4 Cost_P2 ->P1 Cost_P2 ->P2 ... Cost_P2 ->Pp
5 ...
6 Cost_Pp ->P1 Cost_Pp ->P2 ... Cost_Pp ->Pp
7
8 V_ID C a p a c i t GarageOrigine ProduitInitial
9 ...
10
11 D_ID X Y Stock_P1 Stock_P2 ... Stock_Pp
12 ...
13
14 G_ID X Y
15 ...
16
17 S_ID X Y Demande_P1 Demande_P2 ... Demande_Pp
18 ...
```

### 3.1 Détail de Chaque Section

#### 3.1.1 Ligne 1 : Paramètres Globaux


Format :

```text
NbVehicules NbDepots NbGarages NbStations NbProduits
```

Une seule ligne contenant les 5 paramètres globaux, séparés par des tabulations.

| Paramètre   	| Type    	| Description                     	|
|-------------	|---------	|---------------------------------	|
| NbVehicules 	| integer 	| Nombre de véhicules disponibles 	|
| NbDepots    	| integer 	| Nombre de dépôts                	|
| NbGarages   	| integer 	| Nombre de garages (bases)       	|
| NbStations  	| integer 	| Nombre de stations (clients)    	|
| NbProduits  	| integer 	| Nombre de produits à distribuer 	|


#### 3.1.2 Lignes 2 à (1+NbProduits) : Matrice de Coûts de Transition

Format (une ligne par produit source) :
```text
Cost_Pi->P1 Cost_Pi->P2 ... Cost_Pi->Pp
```

La matrice de coûts de transition est une matrice carrée de taille NbProduits × NbProduits exportée par
NumPy. L’élément à la ligne i et colonne j représente le coût de transition du produit Pi au produit Pj. La
diagonale (i=j) est généralement 0. Les colonnes sont séparées par des tabulations.

**Exemple** : Pour 2 produits :
```text
1 0.0 78.
2 60.3 0.
```
Cela signifie : P1→P2 coûte 78.5 et P2→P1 coûte 60.3.

#### 3.1.3 Véhicules

Format (une ligne par véhicule) :
```text
ID Capacité GarageOrigine ProduitInitial
```

Tableau avec NbVehicules lignes et 4 colonnes. Les colonnes sont séparées par des tabulations.

| Champ   	| Type    	| Description                     	|
|-------------	|---------	|---------------------------------	|
| ID 	| integer 	| Identifiant unique du véhicule 	|
| Capacité    	| integer 	| Capacité maximale de chargement (unités)               	|
| GarageOrigine   	| integer 	| ID du garage de départ/retour      	|
| ProduitInitial  	| integer 	| ID du produit initial   	|


**Exemple** :
```text
1 1 20000 2 1
2 2 20000 2 2
```
#### 3.1.4 Dépôts

Format (une ligne par dépôt) :

```text
ID X Y Stock_P1 Stock_P2 ... Stock_Pp
```
Tableau avec NbDepots lignes et (3 + NbProduits) colonnes. Les colonnes sont séparées par des
tabulations.
Les stocks sont listés dans l’ordre des produits. Si un dépôt ne dispose pas d’un produit, sa valeur est 0.

**Exemple** :
```text
1 1 37.3 35.5 56449 86791
```

|Champ   | Type  | Description  |
|---|---|---|
| ID  | int  | Identifiant unique du dépôt  |
| X  | float   | Coordonnée X (position géographique)  |
| Y  | float  | Coordonnée Y (position géographique)  |
| Stock_Pi  | int   | Quantité disponible du produit Pi  |


#### 3.1.5 Garages

Format (une ligne par garage) :

```text
ID X Y
```

Tableau avec NbGarages lignes et 3 colonnes. Les colonnes sont séparées par des tabulations.

|Champ   | Type  | Description                          |
|---|---|--------------------------------------|
| ID  | int  | Identifiant unique du garage         |
| X  | float   | Coordonnée X (position géographique) |
| Y  | float  | Coordonnée Y (position géographique) |



**Exemple** :
```
1 1 50.6 24.
2 2 37.3 17.
```
#### 3.1.6 Stations

Format (une ligne par station) :

```text
ID X Y Demande_P1 Demande_P2 ... Demande_Pp
```

Tableau avec NbStations lignes et (3 + NbProduits) colonnes. Les colonnes sont séparées par des
tabulations.

|Champ   | Type  | Description                          |
|---|---|--------------------------------------|
| ID  | int  | Identifiant unique de la station     |
| X  | float   | Coordonnée X (position géographique) |
| Y  | float  | Coordonnée Y (position géographique) |
| Demande_Pi  | int   | Quantité demandée du produit Pi   |


Les demandes sont listées dans l’ordre des produits. Une demande de 0 signifie que la station n’a pas besoin
de ce produit.

**Exemple** :

```text
1 1 5.6 93.7 1154 0
2 2 44.7 92.5 0 0
3 3 10.8 60.8 2541 0
```
## 4 Exemple Complet

Voici un exemple complet d’un fichier d’instance (MPVRP_4_s3_d1_p2.dat avec 2 véhicules, 1 dépôt, 2
garages, 3 stations, 2 produits) :
```text
1 2 1 2 3 2
2 0.0 78.
3 60.3 0.
4 1 20000 2 1
5 2 20000 2 2
6 1 37.3 35.5 56449 86791
7 1 50.6 24.
8 2 37.3 17.
9 1 5.6 93.7 1154 0
10 2 44.7 92.5 0 0
11 3 10.8 60.8 2541 0
```

**Interprétation** :
- Ligne 1 : 2 véhicules, 1 dépôt, 2 garages, 3 stations, 2 produits
- Lignes 2-3 : Matrice de coûts de transition 2× 2
  - P1→P1 : 0.0, P1→P2 : 78.
  - P2→P1 : 60.3, P2→P2 : 0.
- Lignes 4-5 : 2 véhicules (capacité 20000 chacun)
  - V1 au garage G2, produit initial P
  - V2 au garage G2, produit initial P
- Ligne 6 : Dépôt D1 à position (37.3, 35.5), stocks P1 : 56449, P2 : 86791
- Lignes 7-8 : Garages G1 et G
- Lignes 9-11 : 3 stations avec leurs demandes