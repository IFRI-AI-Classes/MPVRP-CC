# Batch Generator - MPVRP-CC

Générateur automatique d'instances MPVRP-CC par catégorie (Small, Medium, Large).

## 📋 Description

Ce script permet de générer automatiquement **150 instances** réparties en 3 catégories :
- **50 instances Small** → Petites instances de test
- **50 instances Medium** → Instances de taille moyenne
- **50 instances Large** → Grandes instances complexes

Chaque catégorie a ses propres plages de paramètres définies selon les spécifications du projet.

---

## 📊 Spécifications des catégories

| Paramètre | Small | Medium | Large |
|-----------|-------|--------|-------|
| **Stations** | 5 - 15 | 30 - 60 | 100 - 200 |
| **Véhicules** | 2 - 5 | 10 - 20 | 30 - 50 |
| **Produits** | 2 - 3 | 4 - 7 | 8 - 12 |
| **Dépôts** | 1 - 2 | 3 - 5 | 6 - 10 |
| **Garages** | 1 | 2 - 3 | 4 - 8 |
| **Coût transition** | 10 - 50 | 10 - 100 | 10 - 200 |
| **Capacité véhicule** | 1 000 - 5 000 | 10 000 - 40 000 | 10 000 - 80 000 |
| **Demande station** | 500 - 5 000 | 500 - 25 000 | 500 - 75 000 |
| **Taille grille** | 100 | 500 | 1 500 |

---

## 🗂️ Structure de sortie

Les instances sont organisées dans des sous-dossiers par catégorie :

```
data/instances/
├── small/
│   ├── MPVRP_S_001_s8_d1_p2.dat
│   ├── MPVRP_S_002_s12_d2_p3.dat
│   ├── MPVRP_S_003_s5_d1_p2.dat
│   └── ... (50 fichiers)
├── medium/
│   ├── MPVRP_M_001_s45_d4_p5.dat
│   ├── MPVRP_M_002_s38_d3_p6.dat
│   └── ... (50 fichiers)
└── large/
    ├── MPVRP_L_001_s150_d8_p10.dat
    ├── MPVRP_L_002_s120_d7_p9.dat
    └── ... (50 fichiers)
```

### Nomenclature des fichiers

```
MPVRP_{ID}_s{stations}_d{depots}_p{produits}.dat
```

- **ID** : Identifiant unique (S_001 pour Small, M_001 pour Medium, L_001 pour Large)
- **s** : Nombre de stations
- **d** : Nombre de dépôts
- **p** : Nombre de produits

---

## Utilisation

### Commandes de base

#### Générer toutes les instances (150 au total)
```bash
python batch_generator.py
```

#### Générer uniquement une catégorie
```bash
# Uniquement les instances Small (50)
python batch_generator.py --category small

# Uniquement les instances Medium (50)
python batch_generator.py --category medium

# Uniquement les instances Large (50)
python batch_generator.py --category large

# Plusieurs catégories
python batch_generator.py --category small medium
```

#### Modifier le nombre d'instances par catégorie
```bash
# 10 instances par catégorie (30 au total)
python batch_generator.py --count 10

# 100 instances par catégorie (300 au total)
python batch_generator.py --count 100
```

#### Reproductibilité avec seed
```bash
# Utiliser une graine pour générer les mêmes instances
python batch_generator.py --seed 42
```

#### Mode simulation (dry-run)
```bash
# Voir les paramètres sans créer de fichiers
python batch_generator.py --dry-run

# Avec détails
python batch_generator.py --dry-run --verbose
```

#### Écraser les fichiers existants
```bash
python batch_generator.py --force
```

---

## ⚙️ Options disponibles

| Option | Raccourci | Description | Défaut |
|--------|-----------|-------------|--------|
| `--category` | `-c` | Catégorie(s) à générer | toutes |
| `--count` | `-n` | Nombre d'instances par catégorie | 50 |
| `--seed` | | Graine aléatoire pour reproductibilité | None |
| `--dry-run` | | Mode simulation (pas de fichiers créés) | False |
| `--force` | `-f` | Écraser les fichiers existants | False |
| `--verbose` | `-v` | Affichage détaillé | False |

---

## 📝 Exemples complets

### Exemple 1 : Génération standard
```bash
python batch_generator.py
```
**Résultat** : 150 instances créées (50 par catégorie)

### Exemple 2 : Test rapide
```bash
python batch_generator.py --category small --count 5 --verbose
```
**Résultat** : 5 instances Small avec affichage détaillé des paramètres

### Exemple 3 : Génération reproductible
```bash
python batch_generator.py --seed 12345 --count 20
```
**Résultat** : 60 instances identiques à chaque exécution avec cette seed

### Exemple 4 : Vérifier avant de générer
```bash
python batch_generator.py --dry-run --verbose
```
**Résultat** : Affiche tous les paramètres sans créer de fichiers

---

## 📊 Sortie console

### Pendant la génération
```
============================================================
BATCH GENERATOR - MPVRP-CC
Générateur automatique d'instances par catégorie
============================================================
📁 Dossier créé : .../data/instances/small
📁 Dossier créé : .../data/instances/medium
📁 Dossier créé : .../data/instances/large

============================================================
📦 Catégorie : SMALL
   Petites instances (5-15 stations)
   Dossier : .../data/instances/small
   Instances à générer : 50
============================================================
✅ [  1/50] S_001 - s8_d1_p2
✅ [  2/50] S_002 - s12_d2_p3
...
```

### Résumé final
```
============================================================
📊 RÉSUMÉ
============================================================

SMALL:
   ✅ Succès  : 50
   ❌ Échecs  : 0
   ⏭️  Ignorés : 0

MEDIUM:
   ✅ Succès  : 50
   ❌ Échecs  : 0
   ⏭️  Ignorés : 0

LARGE:
   ✅ Succès  : 50
   ❌ Échecs  : 0
   ⏭️  Ignorés : 0

────────────────────────────────────
TOTAL:
   ✅ Succès  : 150
   ❌ Échecs  : 0
   ⏭️  Ignorés : 0

⏱️  Durée totale : 12.34 secondes
============================================================
```

---

## 🔧 Personnalisation

Pour modifier les plages de paramètres, éditez le dictionnaire `CATEGORIES` dans `batch_generator.py` :

```python
CATEGORIES = {
    "small": {
        "description": "Petites instances (5-15 stations)",
        "nb_stations": (5, 15),      # (min, max)
        "nb_vehicules": (2, 5),
        "nb_produits": (2, 3),
        "nb_depots": (1, 2),
        "nb_garages": (1, 1),
        "transition_cost": (10.0, 50.0),
        "capacity": (1000, 5000),
        "demand": (500, 5000),
        "grid_size": 100
    },
    # ... medium, large
}
```

---

## 📁 Fichiers associés

| Fichier | Description |
|---------|-------------|
| `batch_generator.py` | Script principal de génération batch |
| `instance_provider.py` | Générateur d'instance individuelle |
| `instance_verificator.py` | Vérificateur de validité des instances |

---

## ❓ FAQ

### Comment vérifier les instances générées ?
```bash
python instance_verificator.py ../../../data/instances/small/MPVRP_S_001_s8_d1_p2.dat
```

### Les instances sont-elles garanties valides ?
**Oui !** Chaque instance est automatiquement validée après sa génération grâce à `InstanceVerificator`.

**Si une instance échoue la validation**, elle est automatiquement supprimée et comptabilisée comme échec.

### Comment régénérer exactement les mêmes instances ?
Utilisez l'option `--seed` avec la même valeur :
```bash
python batch_generator.py --seed 42
```
