#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Generator - Générateur automatique d'instances MPVRP-CC par catégorie

Ce script génère automatiquement 150 instances réparties en 3 catégories :
- 50 instances Small
- 50 instances Medium  
- 50 instances Large

Chaque catégorie a ses propres plages de paramètres définies.
Les instances sont sauvegardées dans des sous-dossiers dédiés.

Usage:
    python batch_generator.py                    # Génère toutes les catégories (150 instances)
    python batch_generator.py --category small   # Génère uniquement les instances Small
    python batch_generator.py --count 10         # Génère 10 instances par catégorie
    python batch_generator.py --seed 42          # Avec graine pour reproductibilité
"""

import os
import sys
import random
import argparse
from datetime import datetime

# Ajouter le chemin pour importer instance_provider et instance_verificator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instance_provider import generer_instance
from instance_verificator import InstanceVerificator


# =============================================================================
# DÉFINITION DES CATÉGORIES ET LEURS PARAMÈTRES
# =============================================================================

CATEGORIES = {
    "small": {
        "description": "Petites instances (5-15 stations)",
        "nb_stations": (5, 15),
        "nb_vehicules": (2, 5),
        "nb_produits": (2, 3),
        "nb_depots": (1, 2),
        "nb_garages": (1, 1),  # Fixé à 1
        "transition_cost": (10.0, 50.0),
        "capacity": (1000, 5000),
        "demand": (500, 5000),
        "grid_size": 100
    },
    "medium": {
        "description": "Instances moyennes (30-60 stations)",
        "nb_stations": (30, 60),
        "nb_vehicules": (10, 20),
        "nb_produits": (4, 7),
        "nb_depots": (3, 5),
        "nb_garages": (2, 3),
        "transition_cost": (10.0, 100.0),
        "capacity": (10000, 40000),
        "demand": (500, 25000),
        "grid_size": 500
    },
    "large": {
        "description": "Grandes instances (100-200 stations)",
        "nb_stations": (100, 200),
        "nb_vehicules": (30, 50),
        "nb_produits": (8, 12),
        "nb_depots": (6, 10),
        "nb_garages": (4, 8),
        "transition_cost": (10.0, 200.0),
        "capacity": (10000, 80000),
        "demand": (500, 75000),
        "grid_size": 1500
    }
}


def parse_args():
    """Parse les arguments de la ligne de commande"""
    parser = argparse.ArgumentParser(
        description="Générateur batch d'instances MPVRP-CC par catégorie",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python batch_generator.py                         # Génère 50 instances par catégorie (150 total)
  python batch_generator.py --category small        # Génère uniquement 50 Small
  python batch_generator.py --category medium large # Génère Medium et Large
  python batch_generator.py --count 10              # Génère 10 instances par catégorie
  python batch_generator.py --seed 42               # Reproductibilité avec seed
  python batch_generator.py --dry-run               # Simulation sans génération
        """
    )
    
    parser.add_argument(
        '-c', '--category',
        nargs='+',
        choices=['small', 'medium', 'large'],
        default=['small', 'medium', 'large'],
        help="Catégorie(s) à générer (défaut: toutes)"
    )
    
    parser.add_argument(
        '-n', '--count',
        type=int,
        default=50,
        help="Nombre d'instances par catégorie (défaut: 50)"
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help="Graine aléatoire pour reproductibilité"
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Mode simulation : affiche les paramètres sans générer"
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help="Écraser les instances existantes sans confirmation"
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Affichage détaillé"
    )
    
    return parser.parse_args()


def get_category_output_dir(category: str) -> str:
    """
    Retourne le chemin du dossier de sortie pour une catégorie donnée.
    
    Args:
        category: Nom de la catégorie (small, medium, large)
    
    Returns:
        Chemin absolu vers le dossier de la catégorie
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    instances_dir = os.path.join(script_dir, "../../../data/instances", category)
    return os.path.abspath(instances_dir)


def ensure_category_dirs():
    """Crée les dossiers de catégories s'ils n'existent pas"""
    for category in CATEGORIES.keys():
        dir_path = get_category_output_dir(category)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"📁 Dossier créé : {dir_path}")


def validate_instance_silent(filepath: str) -> bool:
    """
    Valide une instance de manière silencieuse (sans affichage).
    
    Utilise InstanceVerificator pour vérifier la validité de l'instance
    sans afficher les messages de vérification.
    
    Args:
        filepath: Chemin vers le fichier .dat à vérifier
    
    Returns:
        True si l'instance est valide, False sinon
    """
    import io
    import sys
    
    # Rediriger stdout pour supprimer les prints
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        verificator = InstanceVerificator(filepath)
        is_valid = verificator.verify()
        return is_valid
    except Exception:
        return False
    finally:
        # Restaurer stdout
        sys.stdout = old_stdout


def generate_random_params(category: str) -> dict:
    """
    Génère des paramètres aléatoires pour une instance selon sa catégorie.
    
    Args:
        category: Nom de la catégorie (small, medium, large)
    
    Returns:
        Dictionnaire des paramètres pour generer_instance()
    """
    config = CATEGORIES[category]
    
    return {
        "nb_s": random.randint(*config["nb_stations"]),
        "nb_v": random.randint(*config["nb_vehicules"]),
        "nb_p": random.randint(*config["nb_produits"]),
        "nb_d": random.randint(*config["nb_depots"]),
        "nb_g": random.randint(*config["nb_garages"]),
        "min_transition_cost": config["transition_cost"][0],
        "max_transition_cost": config["transition_cost"][1],
        "min_capacite": config["capacity"][0],
        "max_capacite": config["capacity"][1],
        "min_demand": config["demand"][0],
        "max_demand": config["demand"][1],
        "max_coord": config["grid_size"]
    }


def generate_instance_id(category: str, index: int) -> str:
    """
    Génère un identifiant unique pour une instance.
    
    Format: {category_prefix}_{index:03d}
    Exemple: S_001, M_025, L_050
    
    Args:
        category: Nom de la catégorie
        index: Numéro de l'instance (1 à N)
    
    Returns:
        Identifiant formaté
    """
    prefix_map = {
        "small": "S",
        "medium": "M",
        "large": "L"
    }
    prefix = prefix_map.get(category, category[0].upper())
    return f"{prefix}_{index:03d}"


def generate_category_instances(category: str, count: int, seed: int = None, 
                                 dry_run: bool = False, force: bool = False,
                                 verbose: bool = False) -> dict:
    """
    Génère toutes les instances d'une catégorie.
    
    Args:
        category: Nom de la catégorie
        count: Nombre d'instances à générer
        seed: Graine aléatoire (optionnel)
        dry_run: Si True, simule sans générer
        force: Si True, écrase les fichiers existants
        verbose: Si True, affiche les détails
    
    Returns:
        Dictionnaire avec statistiques {success: int, failed: int, skipped: int}
    """
    config = CATEGORIES[category]
    output_dir = get_category_output_dir(category)
    
    print(f"\n{'='*60}")
    print(f"📦 Catégorie : {category.upper()}")
    print(f"   {config['description']}")
    print(f"   Dossier : {output_dir}")
    print(f"   Instances à générer : {count}")
    print(f"{'='*60}")
    
    # Initialiser la graine pour cette catégorie
    if seed is not None:
        # Utiliser une graine dérivée pour chaque catégorie
        category_seed = seed + hash(category) % 10000
        random.seed(category_seed)
        print(f"🎲 Seed catégorie : {category_seed}")
    
    stats = {"success": 0, "failed": 0, "skipped": 0, "retries": 0}
    
    # Nombre maximum de tentatives par instance pour éviter boucle infinie
    MAX_RETRIES = 10
    
    i = 1  # Compteur d'instances à générer
    attempt_seed_offset = 0  # Offset pour varier la seed à chaque tentative
    
    while i <= count:
        instance_id = generate_instance_id(category, i)
        params = generate_random_params(category)
        
        # Afficher les paramètres en mode verbose ou dry-run
        if verbose or dry_run:
            print(f"\n[{i}/{count}] Instance {instance_id}")
            print(f"   Stations: {params['nb_s']}, Véhicules: {params['nb_v']}, "
                  f"Produits: {params['nb_p']}, Dépôts: {params['nb_d']}, "
                  f"Garages: {params['nb_g']}")
            print(f"   Capacité: [{params['min_capacite']}, {params['max_capacite']}]")
            print(f"   Demande: [{params['min_demand']}, {params['max_demand']}]")
            print(f"   Coût transition: [{params['min_transition_cost']}, {params['max_transition_cost']}]")
            print(f"   Grille: {params['max_coord']}")
        
        if dry_run:
            stats["skipped"] += 1
            i += 1
            continue
        
        # Tentatives de génération jusqu'à obtenir une instance valide
        instance_created = False
        retries = 0
        
        while not instance_created and retries < MAX_RETRIES:
            try:
                # Générer l'instance avec une seed unique
                current_seed = None
                if seed is not None:
                    current_seed = seed + i + attempt_seed_offset
                
                filepath = generate_single_instance(
                    instance_id=instance_id,
                    params=params,
                    output_dir=output_dir,
                    force=force,
                    seed=current_seed
                )
                
                if filepath:
                    # Valider l'instance avec InstanceVerificator
                    is_valid = validate_instance_silent(filepath)
                    
                    if is_valid:
                        stats["success"] += 1
                        instance_created = True
                        if not verbose:
                            # Affichage compact
                            print(f"✅ [{i:3d}/{count}] {instance_id} - "
                                  f"s{params['nb_s']}_d{params['nb_d']}_p{params['nb_p']}")
                    else:
                        # Instance invalide : supprimer et réessayer avec nouveaux paramètres
                        os.remove(filepath)
                        retries += 1
                        stats["retries"] += 1
                        attempt_seed_offset += 1000  # Changer la seed pour la prochaine tentative
                        params = generate_random_params(category)  # Nouveaux paramètres
                        
                        if verbose:
                            print(f"   ⚠️ Tentative {retries}/{MAX_RETRIES} - Régénération...")
                else:
                    # Échec de génération, réessayer
                    retries += 1
                    stats["retries"] += 1
                    attempt_seed_offset += 1000
                    params = generate_random_params(category)
                    
            except Exception as e:
                retries += 1
                stats["retries"] += 1
                attempt_seed_offset += 1000
                params = generate_random_params(category)
                
                if verbose:
                    print(f"   ⚠️ Erreur tentative {retries}: {str(e)}")
        
        # Si on a épuisé toutes les tentatives sans succès
        if not instance_created:
            stats["failed"] += 1
            print(f"❌ [{i:3d}/{count}] {instance_id} - Échec après {MAX_RETRIES} tentatives")
        
        i += 1  # Passer à l'instance suivante
    
    return stats


def generate_single_instance(instance_id: str, params: dict, output_dir: str,
                              force: bool = False, seed: int = None) -> str:
    """
    Génère une seule instance en déléguant à instance_provider.generer_instance().
    
    Le batch_generator ne se soucie que du tirage aléatoire des paramètres.
    Toute la logique de génération et de faisabilité est gérée par instance_provider.
    
    Args:
        instance_id: Identifiant de l'instance
        params: Paramètres de génération (issus de generate_random_params)
        output_dir: Dossier de sortie
        force: Écraser si existe
        seed: Graine aléatoire
    
    Returns:
        Chemin du fichier généré ou None
    """
    # Construire le chemin attendu pour vérification préalable
    filename = f"MPVRP_{instance_id}_s{params['nb_s']}_d{params['nb_d']}_p{params['nb_p']}.dat"
    filepath = os.path.join(output_dir, filename)
    
    # Vérifier si existe déjà (évite d'appeler generer_instance inutilement)
    if os.path.exists(filepath) and not force:
        print(f"⏭️  Fichier existant ignoré : {filename}")
        return None
    
    # Déléguer la génération à instance_provider (mode silencieux)
    result = generer_instance(
        id_inst=instance_id,
        nb_v=params['nb_v'],
        nb_d=params['nb_d'],
        nb_g=params['nb_g'],
        nb_s=params['nb_s'],
        nb_p=params['nb_p'],
        max_coord=params['max_coord'],
        min_capacite=params['min_capacite'],
        max_capacite=params['max_capacite'],
        min_transition_cost=params['min_transition_cost'],
        max_transition_cost=params['max_transition_cost'],
        min_demand=params['min_demand'],
        max_demand=params['max_demand'],
        seed=seed,
        force_overwrite=force,
        output_dir=output_dir,
        silent=True
    )
    
    return result


def print_summary(all_stats: dict, start_time: datetime, dry_run: bool = False):
    """
    Affiche le résumé final de la génération.
    
    Args:
        all_stats: Dictionnaire {category: stats} pour chaque catégorie
        start_time: Heure de début
        dry_run: Mode simulation
    """
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n{'='*60}")
    print(f"📊 RÉSUMÉ {'(SIMULATION)' if dry_run else ''}")
    print(f"{'='*60}")
    
    total_success = 0
    total_failed = 0
    total_skipped = 0
    total_retries = 0
    
    for category, stats in all_stats.items():
        print(f"\n{category.upper():}")
        print(f"   ✅ Succès  : {stats['success']}")
        print(f"   ❌ Échecs  : {stats['failed']}")
        print(f"   ⏭️  Ignorés : {stats['skipped']}")
        if stats.get('retries', 0) > 0:
            print(f"   🔄 Retries : {stats['retries']}")
        
        total_success += stats['success']
        total_failed += stats['failed']
        total_skipped += stats['skipped']
        total_retries += stats.get('retries', 0)
    
    print(f"\n{'─'*40}")
    print(f"TOTAL:")
    print(f"   ✅ Succès  : {total_success}")
    print(f"   ❌ Échecs  : {total_failed}")
    print(f"   ⏭️  Ignorés : {total_skipped}")
    if total_retries > 0:
        print(f"   🔄 Retries : {total_retries}")
    print(f"\n⏱️  Durée totale : {duration:.2f} secondes")
    print(f"{'='*60}\n")


def print_category_specs():
    """Affiche les spécifications de chaque catégorie"""
    print("\n📋 SPÉCIFICATIONS DES CATÉGORIES")
    print("="*70)
    
    headers = ["Paramètre", "Small", "Medium", "Large"]
    rows = [
        ("Stations", "nb_stations"),
        ("Véhicules", "nb_vehicules"),
        ("Produits", "nb_produits"),
        ("Dépôts", "nb_depots"),
        ("Garages", "nb_garages"),
        ("Coût transition", "transition_cost"),
        ("Capacité véhicule", "capacity"),
        ("Demande station", "demand"),
        ("Taille grille", "grid_size"),
    ]
    
    print(f"{'Paramètre':<20} {'Small':<15} {'Medium':<15} {'Large':<15}")
    print("-"*70)
    
    for label, key in rows:
        values = []
        for cat in ["small", "medium", "large"]:
            val = CATEGORIES[cat][key]
            if isinstance(val, tuple):
                values.append(f"{val[0]} - {val[1]}")
            else:
                values.append(str(val))
        print(f"{label:<20} {values[0]:<15} {values[1]:<15} {values[2]:<15}")
    
    print("="*70 + "\n")


def main():
    """Point d'entrée principal du script"""
    args = parse_args()
    
    print("\n" + "="*60)
    print("BATCH GENERATOR - MPVRP-CC")
    print("Générateur automatique d'instances par catégorie")
    print("="*60)
    
    # Afficher les specs si verbose
    if args.verbose:
        print_category_specs()
    
    # Créer les dossiers de sortie
    ensure_category_dirs()
    
    # Configurer la graine globale
    if args.seed is not None:
        random.seed(args.seed)
        print(f"\n🎲 Graine globale : {args.seed}")
    
    start_time = datetime.now()
    
    if args.dry_run:
        print("\n⚠️  MODE SIMULATION - Aucun fichier ne sera créé")
    
    # Générer les instances pour chaque catégorie sélectionnée
    all_stats = {}
    
    for category in args.category:
        stats = generate_category_instances(
            category=category,
            count=args.count,
            seed=args.seed,
            dry_run=args.dry_run,
            force=args.force,
            verbose=args.verbose
        )
        all_stats[category] = stats
    
    # Afficher le résumé
    print_summary(all_stats, start_time, args.dry_run)
    
    # Code de retour
    total_failed = sum(s['failed'] for s in all_stats.values())
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
