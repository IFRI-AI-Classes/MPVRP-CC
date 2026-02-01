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
1 # UUID (identifiant unique)
2 NbVehicules NbDepots NbGarages NbStations NbProduits
3
4 Cost_P1 ->P1 Cost_P1 ->P2 ... Cost_P1 ->Pp
5 Cost_P2 ->P1 Cost_P2 ->P2 ... Cost_P2 ->Pp
6 ...
7 Cost_Pp ->P1 Cost_Pp ->P2 ... Cost_Pp ->Pp
8
9 V_ID Capacité GarageOrigine ProduitInitial
10 ...
11
12 D_ID X Y Stock_P1 Stock_P2 ... Stock_Pp
13 ...
14
15 G_ID X Y
16 ...
17
18 S_ID X Y Demande_P1 Demande_P2 ... Demande_Pp
19 ...
```

### 3.1 Détail de Chaque Section

#### 3.1.1 Ligne 1 : UUID (Identifiant unique)

Format :

```text
# {UUID-v4}
```

La première ligne contient un commentaire commençant par `#` suivi d'un UUID v4 unique généré pour chaque instance.
Cet identifiant garantit l'unicité globale de l'instance et permet de tracer son origine.

**Exemple** :
```text
# c01ab718-9a2c-4a7d-bb95-f37e2a389409
```

#### 3.1.2 Ligne 2 : Paramètres Globaux

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


#### 3.1.3 Lignes 3 à (2+NbProduits) : Matrice de Coûts de Transition

Format (une ligne par produit source) :
```text
Cost_Pi->P1 Cost_Pi->P2 ... Cost_Pi->Pp
```

La matrice de coûts de transition est une matrice carrée de taille NbProduits × NbProduits exportée par
NumPy. L'élément à la ligne i et colonne j représente le coût de transition du produit Pi au produit Pj. La
diagonale (i=j) est généralement 0. Les colonnes sont séparées par des tabulations.

**Exemple** : Pour 2 produits :
```text
0.0 78.
60.3 0.
```
Cela signifie : P1→P2 coûte 78.0 et P2→P1 coûte 60.3.

#### 3.1.4 Véhicules

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
#### 3.1.5 Dépôts

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


#### 3.1.6 Garages

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
#### 3.1.7 Stations

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
# c01ab718-9a2c-4a7d-bb95-f37e2a389409
2 1 2 3 2
0.0 78.
60.3 0.
1 20000 2 1
2 20000 2 2
1 37.3 35.5 56449 86791
1 50.6 24.
2 37.3 17.
1 5.6 93.7 1154 0
2 44.7 92.5 0 0
3 10.8 60.8 2541 0
```

**Interprétation** :
- Ligne 1 : UUID unique de l'instance
- Ligne 2 : 2 véhicules, 1 dépôt, 2 garages, 3 stations, 2 produits
- Lignes 3-4 : Matrice de coûts de transition 2× 2
  - P1→P1 : 0.0, P1→P2 : 78.
  - P2→P1 : 60.3, P2→P2 : 0.
- Lignes 5-6 : 2 véhicules (capacité 20000 chacun)
  - V1 au garage G2, produit initial P1
  - V2 au garage G2, produit initial P2
- Ligne 7 : Dépôt D1 à position (37.3, 35.5), stocks P1 : 56449, P2 : 86791
- Lignes 8-9 : Garages G1 et G2
- Lignes 10-12 : 3 stations avec leurs demandes
- Lignes 9-11 : 3 stations avec leurs demandes