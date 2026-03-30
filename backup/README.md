# Documentation technique du module backup

Ce dossier contient l'implémentation d'une api web et des modules métier pour le problème MPVRP-CC (Multi-Product Vehicle Routing Problem with Compartment Constraints). Il s'agit d'une variante du problème de tournées de véhicules où les véhicules à compartiment unique transportent plusieurs types de produits avec des coûts de transition entre les produits.

## Structure du dossier

```
backup/
├── __init__.py
├── app/                    # Application web FastAPI
│   ├── __init__.py
│   ├── main.py             # Point d'entrée de l'api
│   ├── schemas.py          # Schémas Pydantic pour la validation
│   ├── utils.py            # Utilitaires (vide actuellement)
│   └── routes/
│       ├── __init__.py
│       ├── generator.py    # Endpoint de génération d'instances
│       └── model.py        # Endpoint de vérification de solutions
└── core/                   # Logique métier
    ├── __init__.py
    ├── generator/          # Génération d'instances
    │   ├── __init__.py
    │   ├── batch_generator.py      # Génération par lots
    │   ├── instance_provider.py    # Génération unitaire
    │   ├── instance_verificator.py # Validation d'instances
    │   └── README.md
    └── model/              # Modélisation et résolution
        ├── __init__.py
        ├── feasibility.py  # Vérification de faisabilité
        ├── modelisation.py # Modèle MIP avec PuLP
        ├── schemas.py      # Classes de données
        └── utils.py        # Parsing et calculs auxiliaires
```

---

## Module app

### main.py

Configure une application FastAPI avec deux groupes de routes :

- `/generator` : génération d'instances MPVRP-CC
- `/model` : vérification de solutions

Le middleware CORS est configuré pour accepter toutes les origines. Deux endpoints utilitaires sont disponibles à la racine :

- `GET /` : retourne les informations de l'api
- `GET /health` : vérification de l'état de santé

### schemas.py

Définit les schémas de validation avec Pydantic :

**InstanceGenerationRequest** : paramètres pour générer une instance
- `id_instance` : identifiant de l'instance
- `nb_vehicules`, `nb_depots`, `nb_garages`, `nb_stations`, `nb_produits` : dimensions du problème
- `max_coord` : taille de la grille (défaut 100.0)
- `min_capacite`, `max_capacite` : bornes de capacité des véhicules
- `min_transition_cost`, `max_transition_cost` : bornes des coûts de changement de produit
- `min_demand`, `max_demand` : bornes des demandes
- `seed` : graine pour reproductibilité

**InstanceGenerationResponse** : contient le nom du fichier et son contenu

**SolutionVerificationResponse** : résultat de vérification avec indicateur de faisabilité, liste d'erreurs et métriques calculées

### routes/generator.py

Endpoint `POST /generator/generate` qui génère une instance MPVRP-CC. Utilise un dossier temporaire pour la génération, puis retourne le fichier en téléchargement direct via `StreamingResponse`.

### routes/model.py

Endpoint `POST /model/verify` qui vérifie la faisabilité d'une solution. Accepte deux fichiers en upload : le fichier d'instance et le fichier de solution. Les fichiers sont sauvegardés temporairement, parsés, puis vérifiés via le module `feasibility`. Les fichiers temporaires sont supprimés après traitement.

---

## Module core/generator

### instance_provider.py

Fonction principale `generer_instance()` qui crée un fichier d'instance MPVRP-CC. Supporte deux modes :

- **mode interactif** : si certains paramètres sont `None`, demande les valeurs à l'utilisateur
- **mode programmatique** : utilise les paramètres fournis directement

Le générateur effectue les opérations suivantes :
1. Génération d'un uuid v4 pour l'instance
2. Création de la matrice de coûts de transition (symétrique, diagonale nulle)
3. Génération des véhicules avec capacité, garage assigné et produit initial
4. Génération des stations avec au moins une demande non-nulle par station
5. Génération des dépôts avec stocks suffisants pour couvrir les demandes
6. Génération des garages
7. Validation de l'instance avant écriture

La fonction `validate_instance()` vérifie :
- Nombre minimum d'entités (au moins 1 de chaque type)
- Unicité et contiguïté des identifiants
- Existence des garages référencés par les véhicules
- Validité des produits initiaux
- Diagonale nulle de la matrice de transition
- Faisabilité des stocks par rapport aux demandes
- Capacités positives
- Demandes non-nulles pour chaque station

Utilisation en ligne de commande :
```bash
python instance_provider.py -i 01 -v 3 -d 2 -g 2 -s 5 -p 3
python instance_provider.py -i 01 -v 3 -d 2 -g 2 -s 5 -p 3 --grid 200 --seed 42
```

### batch_generator.py

Génère des instances par lots selon trois catégories prédéfinies :

| Catégorie | Stations | Véhicules | Produits | Dépôts | Garages | Grille |
|-----------|----------|-----------|----------|--------|---------|--------|
| small     | 5-15     | 2-5       | 2-3      | 1-2    | 1       | 100    |
| medium    | 30-60    | 10-20     | 4-7      | 3-5    | 2-3     | 500    |
| large     | 100-200  | 30-50     | 8-12     | 6-10   | 4-8     | 1500   |

Chaque catégorie a également des plages spécifiques pour les coûts de transition, capacités et demandes.

Les fichiers sont nommés selon le format `MPVRP_{prefix}_{index:03d}_s{nb_s}_d{nb_d}_p{nb_p}.dat` où prefix est S, M ou L selon la catégorie.

Utilisation :
```bash
python batch_generator.py                         # 50 instances par catégorie
python batch_generator.py --category small        # uniquement small
python batch_generator.py --count 10 --seed 42    # 10 instances avec reproductibilité
python batch_generator.py --dry-run               # simulation sans génération
```

### instance_verificator.py

Classe `InstanceVerificator` qui valide un fichier d'instance existant. Les vérifications incluent :

- Existence et format du fichier
- Nombre de lignes correct selon les paramètres
- Éléments minimums requis
- Unicité et contiguïté des identifiants
- Validité des références (garages utilisés, produits initiaux)
- Matrice de transition correctement dimensionnée et diagonale nulle
- Demandes non-nulles pour chaque station
- Faisabilité stocks >= demandes
- Capacité de la flotte suffisante
- Chevauchement géographique (distance minimale entre points)
- Inégalité triangulaire sur la matrice de transition

Utilisation :
```python
verificator = InstanceVerificator("chemin/vers/instance.dat")
is_valid = verificator.verify()
```

---

## Module core/model

### schemas.py

Définit les structures de données avec `dataclass` :

**Camion** : identifiant, capacité, garage assigné, produit initial

**Depot** : identifiant, coordonnées (x, y), stocks par produit

**Garage** : identifiant, coordonnées (x, y)

**Station** : identifiant, coordonnées (x, y), demandes par produit

**Instance** : regroupe toutes les données du problème avec les matrices de coûts et de distances

**ParsedSolutionVehicle** : représente la tournée d'un véhicule dans une solution parsée

**ParsedSolutionDat** : solution complète avec liste des véhicules et métriques

### utils.py

Fonctions utilitaires pour le parsing et les calculs :

**euclidean_distance(point1, point2)** : calcule la distance euclidienne entre deux points 2D

**parse_instance(filepath)** : lit un fichier `.dat` et retourne un objet `Instance`. Le format attendu est :
1. Commentaire avec uuid (optionnel)
2. Ligne de paramètres : nb_produits, nb_depots, nb_garages, nb_stations, nb_vehicules
3. Matrice de transition (nb_produits lignes)
4. Véhicules (nb_vehicules lignes) : id, capacité, garage, produit_initial
5. Dépôts (nb_depots lignes) : id, x, y, stocks...
6. Garages (nb_garages lignes) : id, x, y
7. Stations (nb_stations lignes) : id, x, y, demandes...

**compute_distances(instance)** : calcule la matrice des distances euclidiennes entre tous les noeuds

**parse_solution(filepath)** : lit un fichier solution `.dat`. Le format attendu est :
- Blocs de 2 lignes par véhicule :
  - Ligne route : `k: noeud1 - noeud2 - ... - noeudN`
  - Ligne produits : `k: p1(cout) - p2(cout) - ...`
- 6 lignes de métriques finales

**solution_node_key(kind, node_id)** : convertit un type et id en clé formatée (ex: "depot", 3 → "D3")

### feasibility.py

Fonction `verify_solution(instance, solution)` qui vérifie la faisabilité d'une solution. Retourne une liste d'erreurs (vide si faisable) et un dictionnaire de métriques recalculées.

Vérifications effectuées :
1. Cohérence des véhicules : chaque véhicule part et revient à son garage attitré
2. Respect des capacités : quantité chargée ≤ capacité du véhicule
3. Conservation de la masse : quantité chargée = quantité livrée par segment
4. Satisfaction de la demande : chaque station reçoit exactement ce qu'elle demande
5. Respect des stocks : pas de dépassement des stocks disponibles aux dépôts
6. Validation des métriques : comparaison entre valeurs du fichier et valeurs recalculées

Les métriques recalculées sont :
- `used_vehicles` : nombre de véhicules utilisés
- `total_changes` : nombre de changements de produit
- `total_switch_cost` : coût total des changements
- `distance_total` : distance totale parcourue

