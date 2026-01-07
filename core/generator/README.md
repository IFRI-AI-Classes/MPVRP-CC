# README - Générateur et vérificateur d'instances MPVRP-CC

## Vue d'ensemble
Ce module contient les outils de **génération** et de **vérification** d'instances pour le problème **Multi-Product Vehicle Routing Problem with Changeover Cost** (MPVRP-CC).

---

# 1. Générateur d'instances (`instance_provider.py`)

## Modes d'utilisation

### Mode interactif
```bash
python instance_provider.py
```
Suivre les instructions pour saisir les paramètres un par un.

### Mode ligne de commande
```bash
python instance_provider.py -i <id> -v <véhicules> -d <dépôts> -g <garages> -s <stations> -p <produits>
```

**Exemples :**
```bash
# Instance basique.
python instance_provider.py -i 01 -v 3 -d 2 -g 2 -s 5 -p 3

# Avec options avancées.
python instance_provider.py -i 02 -v 5 -d 3 -g 2 -s 10 -p 4 --grid 200 --seed 42

# Écraser un fichier existant.
python instance_provider.py -i 01 -v 3 -d 2 -g 2 -s 5 -p 3 --force
```

### Options disponibles

| Option | Abréviation | Description | Défaut |
|--------|-------------|-------------|--------|
| `--id` | `-i` | Identifiant de l'instance | - |
| `--vehicles` | `-v` | Nombre de véhicules | - |
| `--depots` | `-d` | Nombre de dépôts | - |
| `--garages` | `-g` | Nombre de garages | - |
| `--stations` | `-s` | Nombre de stations | - |
| `--products` | `-p` | Nombre de produits | - |
| `--grid` | - | Taille de la grille (coordonnées) | 100 |
| `--min-capacity` | - | Capacité minimale véhicule | 10000 |
| `--max-capacity` | - | Capacité maximale véhicule | 25000 |
| `--max-demand` | - | Demande maximale par station | 5000 |
| `--seed` | - | Graine aléatoire (reproductibilité) | - |
| `--force` | `-f` | Écraser fichier existant | False |

## Structure de génération

### Étape 1 : Paramètres d'entrée
- Identifiant de l'instance
- Nombre de véhicules, dépôts, garages, stations, produits
- Taille de la grille de coordonnées

### Étape 2 : Génération des données

**Matrice de coûts de transition** (produit → produit).
- Diagonale : 0 (pas de coût pour même produit).
- Autres cases : coûts aléatoires entre 10 et 80.

**Véhicules** (flotte hétérogène).
- ID unique séquentiel.
- Capacité variable : [min_capacite, max_capacite].
- Garage de départ : assigné aléatoirement parmi les garages existants.
- Produit initial : assigné aléatoirement parmi les produits.

**Stations** (clients).
- ID unique séquentiel.
- Coordonnées (x, y) aléatoires dans la grille.
- Demandes par produit : 0 ou [500, max_demand] unités.

**Dépôts** (approvisionnement).
- ID unique séquentiel.
- Coordonnées (x, y) aléatoires.
- Stocks calculés pour **garantir la faisabilité** : 
  - `stock[p] = demande_totale[p] / nb_dépôts + marge_aléatoire`

**Garages** (points de départ/retour).
- ID unique séquentiel.
- Coordonnées (x, y) aléatoires uniquement.

### Étape 3 : Validation interne
Avant écriture, le générateur valide automatiquement l'instance (voir section Synthèse).

### Étape 4 : Vérification ID unique
- **L'ID doit être unique** parmi tous les fichiers d'instances existants.
- Deux fichiers avec métadonnées différentes mais même ID = **erreur**.
- Liste des IDs existants affichée en cas de conflit.

### Étape 5 : Vérification fichier existant
- Si le fichier existe en **mode interactif** : demande confirmation ou nouvel ID
- Si le fichier existe en **mode CLI** : erreur sauf si `--force` est utilisé

### Étape 6 : Génération UUID v4
- Un **UUID v4 unique** est généré pour chaque instance
- Garantit l'unicité absolue même en cas de métadonnées identiques
- Écrit en commentaire à la première ligne du fichier

### Étape 7 : Écriture du fichier
Format de sortie : `MPVRP_{id}_s{stations}_d{depots}_p{produits}.dat`

Emplacement : `data/instances/`

---

# 2. Vérificateur d'instances (`instance_verificator.py`)

## Utilisation
```bash
python instance_verificator.py <chemin_fichier>
```

**Exemple :**
```bash
python instance_verificator.py ../../data/instances/MPVRP_01_s5_d2_p3.dat
```

## Vérifications effectuées

### 2.1 Vérifications structurelles
- ✅ Existence du fichier
- ✅ Format du fichier (nombre de sections suffisant)
- ✅ Parsing correct des données

### 2.2 Vérifications minimales
- ✅ Au moins 1 véhicule
- ✅ Au moins 1 dépôt
- ✅ Au moins 1 garage
- ✅ Au moins 1 station
- ✅ Au moins 1 produit

### 2.3 Vérifications des IDs
- ✅ IDs véhicules uniques ET contigus [1, nb_v]
- ✅ IDs dépôts uniques ET contigus [1, nb_d]
- ✅ IDs garages uniques ET contigus [1, nb_g]
- ✅ IDs stations uniques ET contigus [1, nb_s]

### 2.4 Vérifications de validité
- ✅ Garages utilisés par véhicules existent
- ✅ Produits initiaux des véhicules sont valides
- ✅ Matrice de transition carrée (nb_p × nb_p)
- ✅ Diagonale de la matrice de transition = 0
- ✅ Au moins une station avec demande > 0
- ✅ Stocks des dépôts non-négatifs

### 2.5 Vérifications de capacité
- ✅ **Demande ≤ Capacité totale flotte** : Chaque demande par station/produit ne doit pas dépasser la capacité cumulée de tous les camions (Split Delivery : un camion ne dessert une station qu'une fois par produit, mais plusieurs camions peuvent desservir la même station)

### 2.6 Vérifications géographiques
- ⚠️ **Chevauchement** : Avertissement si deux points sont à distance < 0.1

### 2.7 Vérification inégalité triangulaire
- ⚠️ **Inégalité triangulaire** : Vérifie que pour tout triplet (i, j, k) :
  
  $$Cost(P_i \to P_k) \leq Cost(P_i \to P_j) + Cost(P_j \to P_k)$$
  
  - Si **non respectée** : Avertissement (pas erreur bloquante)
  - **Raison** : Dans la réalité, certains nettoyages directs peuvent être plus coûteux qu'un passage intermédiaire (chimie complexe)
  - **Impact** : Le solveur pourrait exploiter des "changements fantômes" pour économiser sur les coûts de nettoyage

### 2.8 Vérifications de faisabilité
- ✅ Stock total ≥ Demande totale (par produit)

### 2.9 Vérifications géométriques
- ✅ Pas de valeurs NaN ou Inf
- ✅ Coordonnées non-négatives (avertissement si négatif)
- ✅ Capacités des véhicules strictement positives

## Format de sortie
```
==================================================
📊 RAPPORT DE VÉRIFICATION
==================================================

✅ Aucune erreur critique !
⚠️ X avertissement(s) : ...

Statut : ✅ VALIDE / ❌ INVALIDE
Faisabilité : ✅ FAISABLE / ⚠️ À vérifier
==================================================
```

---

# 3. Synthèse des vérifications

## Comparaison provider vs vérificateur

| Vérification | Provider | Vérificateur | Description |
|--------------|:--------:|:------------:|-------------|
| **Éléments minimaux** | ✅ | ✅ | nb_v, nb_d, nb_g, nb_s, nb_p ≥ 1 |
| **IDs uniques** | ✅ | ✅ | Pas de doublons d'IDs par entité |
| **IDs contigus [1,n]** | ✅ | ✅ | IDs dans l'intervalle attendu |
| **Garages valides** | ✅ | ✅ | Garages des véhicules existent |
| **Produits initiaux valides** | ✅ | ✅ | Produits ∈ [1, nb_p] |
| **Diagonale matrice = 0** | ✅ | ✅ | Pas de coût pour même produit |
| **Faisabilité stocks** | ✅ | ✅ | Stock ≥ Demande par produit |
| **Capacités positives** | ✅ | ✅ | Capacités véhicules > 0 |
| **Demande ≤ Capacité max** | ✅ | ✅ | Chaque demande ≤ plus grand camion |
| **Chevauchement géographique** | ⚠️ | ⚠️ | Avertissement si dist < 0.1 |
| **Inégalité triangulaire** | ❌ | ⚠️ | Avertissement si Cost(i→k) > Cost(i→j) + Cost(j→k) |
| **Fichier existant** | ✅ | ❌ | Vérification avant écrasement |
| **Existence fichier** | ❌ | ✅ | Fichier .dat existe |
| **Format fichier (nb lignes)** | ❌ | ✅ | Nombre exact de lignes attendu |
| **Matrice carrée** | ❌ | ✅ | Dimensions nb_p × nb_p |
| **Demandes existantes** | ❌ | ✅ | Au moins 1 station avec demande |
| **Stocks non-négatifs** | ❌ | ✅ | Stocks dépôts ≥ 0 |
| **Valeurs NaN/Inf** | ❌ | ✅ | Pas de valeurs invalides |
| **Coordonnées valides** | ❌ | ⚠️ | Avertissement si négatif |

### Légende
- ✅ : Vérification effectuée (erreur si échec)
- ⚠️ : Avertissement seulement
- ❌ : Non vérifié par ce module

## Cas d'usage recommandé

```
┌─────────────────────────────────────────────────────────────┐
│                 WORKFLOW RECOMMANDÉ                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Génération    ──►  instance_provider.py                 │
│     (validation interne automatique)                        │
│                           │                                 │
│                           ▼                                 │
│  2. Vérification  ──►  instance_verificator.py              │
│     (validation complète post-génération ou import externe) │
│                           │                                 │
│                           ▼                                 │
│  3. Utilisation   ──►  mpvrp_solver.py                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Quand utiliser le vérificateur ?**
- Après import d'une instance externe
- Pour valider une instance modifiée manuellement
- Pour diagnostiquer une instance problématique
- En complément du provider pour une double vérification

---

# 4. Format du fichier d'instance (.dat)

```
# UUID v4 (commentaire - identifiant unique)
Ligne 1 : [nb_produits  nb_dépôts  nb_garages  nb_stations  nb_véhicules]

Bloc 2  : Matrice de transition (nb_p lignes × nb_p colonnes)

Bloc 3  : Véhicules (nb_v lignes)
          [ID  Capacité  Garage  Produit_initial]

Bloc 4  : Dépôts (nb_d lignes)
          [ID  X  Y  Stock_P1  Stock_P2  ...  Stock_Pn]

Bloc 5  : Garages (nb_g lignes)
          [ID  X  Y]

Bloc 6  : Stations (nb_s lignes)
          [ID  X  Y  Demande_P1  Demande_P2  ...  Demande_Pn]
```

**Séparateur** : Tabulation (`\t`)