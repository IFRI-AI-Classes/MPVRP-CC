# README - Générateur d'Instances MPVRP-CC

## Vue d'ensemble
Générateur d'instances pour le problème **Multi-Product Vehicle Routing Problem with Cross-docking and Contamination costs** (MPVRP-CC).

## Structure du code

### **Niveau 1 : Saisie des paramètres**
- Identifiant de l'instance
- Nombre de véhicules, dépôts, garages, stations, produits
- Taille de la grille de coordonnées

### **Niveau 2 : Génération des données**

**Matrice de coûts de transition** (produit → produit)
- Diagonale : 0 (même produit)
- Autres : coûts aléatoires entre 10 et 80

**Véhicules** (flotte hétérogène)
- Capacité variable : 10 000 à 25 000 unités
- Garage de départ assigné aléatoirement
- Produit initial à bord

**Stations** (clients)
- Coordonnées (x, y) aléatoires
- Demandes par produit : 0 ou [500, 5000] unités

**Dépôts** (approvisionnement)
- Stocks calculés pour **garantir la faisabilité** : chaque dépôt a suffisamment de stock pour couvrir sa part de la demande totale + marge de sécurité

**Garages** (points de départ/retour)
- Coordonnées (x, y) aléatoires uniquement

### **Niveau 3 : Écriture du fichier**
Format : `MPVRP_{id}_s{stations}_d{depots}_p{produits}.dat`

**Structure du fichier :**
```
Ligne 1 : [nb_produits, nb_dépôts, nb_garages, nb_stations, nb_véhicules]
Matrice transition costs (nb_p × nb_p)
Table véhicules
Table dépôts (avec stocks)
Table garages
Table stations (avec demandes)
```

## Utilisation
```bash
python instance_provider.py
```

Suivre les instructions pour saisir les paramètres. Le fichier est créé dans `./Instances/`