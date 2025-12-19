# MPVRP-CRP Solver

Ce projet implémente un solveur pour le **Problème de Tournée de Véhicules Multi-Produits Multi-Dépôts avec Coûts de Changement de Produit (MPVRP-CRP)**. Il utilise la programmation linéaire en nombres entiers mixtes (PLNEM) via la librairie PuLP pour trouver des solutions optimales.

Le projet inclut également un outil de visualisation interactif pour analyser les tournées générées.

## Structure du Projet

- **`mpvrp_solver.py`** : Le script principal du solveur.
- **`mpvrp_verify_v2.py`** : Pour vérifier la validité d'une solution (continuité des trajets, respect des capacités, stocks, demandes).
- **`vrp_professional.html`** : L'interface de visualisation des solutions.
- **`data/`** : Dossier contenant les instances du problème (fichiers `.dat`).
- **`solutions/`** : Dossier où sont exportées les solutions (fichiers `.json`).
- **`visu/`** : Dossier pour les ressources de visualisation.

## Installation

Assurez-vous d'avoir Python installé (3.8+ recommandé).

Installez les dépendances nécessaires :

```bash
pip install pulp networkx
```

## Utilisation

### 1. Résolution d'une instance

1.  Placez vos fichiers d'instance (`.dat`) dans le dossier `data/`.
2.  Lancez le solveur :
    ```bash
    python mpvrp_solver.py
    ```
3.  Le programme listera les fichiers disponibles. Entrez le nom du fichier souhaité (ex: `MPVRP_3_s3_d1_p2.dat`).
4.  La solution sera calculée et exportée automatiquement dans le dossier `solutions/` au format JSON.

### 2. Visualisation

1.  Ouvrez le fichier `vrp_professional.html` dans un navigateur web moderne (Chrome, Firefox, Edge).
2.  Glissez-déposez le fichier d'instance (`.dat` ou `.json`) dans la zone **Instance File**.
3.  Glissez-déposez le fichier de solution généré (`.json` depuis le dossier `solutions/`) dans la zone **Solution File**.
4.  Utilisez les contrôles de lecture pour animer les tournées des véhicules.
### 3. Vérification de la solution

1.  Lancez le script de vérification :
    ```bash
    python mpvrp_verify_v2.py
    ```
2.  Entrez le nom du fichier instance (ex: `MPVRP_3_s3_d1_p2.dat`).
3.  Le script chargera automatiquement la solution correspondante dans `solutions/` et affichera un rapport détaillé.
## Format des Fichiers

### Fichiers d'Instance (`.dat`)
Le format attendu est le suivant :
- **Ligne 1** : Dimensions (`NbVéhicules NbDépôts NbProduits NbStations NbGarages`)
- **Lignes suivantes** : Matrice des coûts de changement de produit.
- **Lignes suivantes** : Définition des véhicules.
- **Lignes suivantes** : Définition des dépôts (ID, X, Y, Stocks...).
- **Lignes suivantes** : Définition des garages (ID, X, Y).
- **Lignes suivantes** : Définition des stations (ID, X, Y, Demandes...).

### Fichiers de Solution (`.json`)
Contient la structure complète de la solution :
- `objective` : Valeur de la fonction objectif (coût total).
- `status` : Statut de la résolution (Optimal, Infeasible...).
- `routes` : Détail des itinéraires par véhicule, ordonnés chronologiquement.
- `summary` : Résumés des livraisons, chargements et changements de produits.

## Technologies

- **Python** : Langage de programmation.
- **PuLP** : Modélisation et résolution de problèmes d'optimisation.
- **HTML5/JS/Canvas** : Visualisation interactive.
