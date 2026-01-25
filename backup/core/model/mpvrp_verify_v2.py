"""MPVRP-CC vérificateur (format README .dat).

Non-conformités corrigées par rapport à l'ancien vérificateur:
- L'instance est parsée via `backup.core.model.utils.parse_instance` (mêmes IDs que `modelisation.py`).
- La solution vérifiée est le fichier `.dat` exporté (format `data/solutions/README.md`).
"""

from __future__ import annotations

import argparse

from typing import Any, Dict, List, Tuple

from .utils import (
    parse_instance,
    parse_solution_dat,
    solution_node_key,
    ParsedSolutionDat,
)


def verify_solution_dat(instance, solution: ParsedSolutionDat) -> Tuple[List[str], Dict[str, Any]]:
    """Vérifie une solution `.dat` (format README) par rapport à l'instance.

    Retourne (errors, computed_metrics).
    """
    errors: List[str] = []

    # Lookups
    vehicle_by_id = {int(k[1:]): v for k, v in instance.camions.items()}
    depot_by_id = {int(k[1:]): v for k, v in instance.depots.items()}
    station_by_id = {int(k[1:]): v for k, v in instance.stations.items()}

    deliveries: Dict[Tuple[str, int], float] = {}
    loads: Dict[Tuple[str, int], float] = {}
    computed_total_changes = 0
    computed_total_switch_cost = 0.0
    computed_distance_total = 0.0

    for v in solution.vehicles:
        camion = vehicle_by_id.get(v.vehicle_id)
        if camion is None:
            errors.append(f"Véhicule {v.vehicle_id}: absent de l'instance")
            continue

        if len(v.nodes) != len(v.products):
            errors.append(
                f"Véhicule {v.vehicle_id}: route/product length mismatch ({len(v.nodes)} vs {len(v.products)})"
            )
            continue

        keyed_nodes = [solution_node_key(n["kind"], n["id"]) for n in v.nodes]
        if not keyed_nodes:
            errors.append(f"Véhicule {v.vehicle_id}: route vide")
            continue

        expected_garage = camion.garage_id
        if keyed_nodes[0] != expected_garage or keyed_nodes[-1] != expected_garage:
            errors.append(
                f"Véhicule {v.vehicle_id}: garage incohérent (attendu {expected_garage}, got {keyed_nodes[0]}..{keyed_nodes[-1]})"
            )

        # Distance
        for a, b in zip(keyed_nodes, keyed_nodes[1:]):
            computed_distance_total += float(instance.distances.get((a, b), 0.0))

        # Switches (produits export 0-based)
        products_only = [p for (p, _c) in v.products]
        for prev_p, cur_p in zip(products_only, products_only[1:]):
            if prev_p != cur_p:
                computed_total_changes += 1
                computed_total_switch_cost += float(instance.costs.get((prev_p, cur_p), 0.0))

        # Segments: dépôt[load] puis stations(deliv) jusqu'au prochain dépôt
        current_segment_load = None  # (depot_key, product, qty)
        current_segment_delivered = 0.0

        for idx, (node, (p, _cumul)) in enumerate(zip(v.nodes, v.products)):
            kind = node["kind"]
            key = solution_node_key(kind, node["id"])
            qty = float(node.get("qty", 0))

            if kind == "depot":
                if node["id"] not in depot_by_id:
                    errors.append(f"Véhicule {v.vehicle_id}: dépôt inconnu D{node['id']}")
                if qty > float(camion.capacity) + 1e-6:
                    errors.append(
                        f"Véhicule {v.vehicle_id}: capacité dépassée au dépôt {key} (chargé={qty}, cap={camion.capacity})"
                    )

                loads[(key, p)] = loads.get((key, p), 0.0) + qty

                if current_segment_load is not None:
                    dkey, pp, expected_qty = current_segment_load
                    if abs(current_segment_delivered - expected_qty) > 1e-2:
                        errors.append(
                            f"Véhicule {v.vehicle_id}: conservation masse segment {dkey} prod {pp} (chargé={expected_qty}, livré={current_segment_delivered})"
                        )

                current_segment_load = (key, p, qty)
                current_segment_delivered = 0.0

            elif kind == "station":
                if node["id"] not in station_by_id:
                    errors.append(f"Véhicule {v.vehicle_id}: station inconnue S{node['id']}")
                deliveries[(key, p)] = deliveries.get((key, p), 0.0) + qty
                current_segment_delivered += qty

            else:
                if idx != 0 and idx != len(v.nodes) - 1:
                    errors.append(f"Véhicule {v.vehicle_id}: garage au milieu de la route (pos {idx+1})")

        if current_segment_load is not None:
            dkey, pp, expected_qty = current_segment_load
            if abs(current_segment_delivered - expected_qty) > 1e-2:
                errors.append(
                    f"Véhicule {v.vehicle_id}: conservation masse segment {dkey} prod {pp} (chargé={expected_qty}, livré={current_segment_delivered})"
                )

    # Demand satisfaction (instance demande 0-based)
    for st in instance.stations.values():
        for p, demand in st.demand.items():
            if demand <= 0:
                continue
            delivered = deliveries.get((st.id, p), 0.0)
            if abs(delivered - float(demand)) > 1e-2:
                errors.append(f"Demande: {st.id} prod {p} (demande={demand}, livré={delivered})")

    # Stock (instance stock 0-based)
    for d in instance.depots.values():
        for p, stock in d.stocks.items():
            taken = loads.get((d.id, p), 0.0)
            if taken - float(stock) > 1e-2:
                errors.append(f"Stock: {d.id} prod {p} (stock={stock}, prélevé={taken})")

    computed = {
        "used_vehicles": len(solution.vehicles),
        "total_changes": computed_total_changes,
        "total_switch_cost": computed_total_switch_cost,
        "distance_total": computed_distance_total,
    }

    # Compare metrics with tolerances (export rounded)
    if solution.metrics.get("used_vehicles") != computed["used_vehicles"]:
        errors.append(
            f"Métrique used_vehicles: fichier={solution.metrics.get('used_vehicles')} calculé={computed['used_vehicles']}"
        )
    if solution.metrics.get("total_changes") != computed["total_changes"]:
        errors.append(
            f"Métrique total_changes: fichier={solution.metrics.get('total_changes')} calculé={computed['total_changes']}"
        )
    if abs(float(solution.metrics.get("total_switch_cost", 0.0)) - computed["total_switch_cost"]) > 0.2:
        errors.append(
            f"Métrique total_switch_cost: fichier={solution.metrics.get('total_switch_cost')} calculé={computed['total_switch_cost']:.2f}"
        )
    if abs(float(solution.metrics.get("distance_total", 0.0)) - computed["distance_total"]) > 0.2:
        errors.append(
            f"Métrique distance_total: fichier={solution.metrics.get('distance_total')} calculé={computed['distance_total']:.2f}"
        )

    return errors, computed


def main(instance_path: str, solution_path: str) -> int:
    instance = parse_instance(instance_path)
    solution = parse_solution_dat(solution_path)
    errors, computed = verify_solution_dat(instance, solution)

    print("=" * 60)
    print("VÉRIFICATION SOLUTION (.dat)")
    print("=" * 60)
    print(f"Instance: {instance_path}")
    print(f"Solution: {solution_path}")
    print("")
    print("Métriques fichier:")
    print(f"  used_vehicles:     {solution.metrics['used_vehicles']}")
    print(f"  total_changes:     {solution.metrics['total_changes']}")
    print(f"  total_switch_cost: {solution.metrics['total_switch_cost']}")
    print(f"  distance_total:    {solution.metrics['distance_total']}")
    print("")
    print("Métriques recalculées:")
    print(f"  used_vehicles:     {computed['used_vehicles']}")
    print(f"  total_changes:     {computed['total_changes']}")
    print(f"  total_switch_cost: {computed['total_switch_cost']:.2f}")
    print(f"  distance_total:    {computed['distance_total']:.2f}")

    if errors:
        print("")
        print(f"❌ SOLUTION NON VALIDE ({len(errors)} erreur(s))")
        for e in errors:
            print(f"- {e}")
        return 1

    print("")
    print("✅ SOLUTION VALIDE ET CONFORME")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vérifie une solution MPVRP-CC au format README (.dat).")
    parser.add_argument("--instance", default="data/instances/MPVRP_01_s5_d2_p2.dat")
    parser.add_argument("--solution", default="data/solutions/Sol_MPVRP_01_s5_d2_p2.dat")
    args = parser.parse_args()
    raise SystemExit(main(args.instance, args.solution))
