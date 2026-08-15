"""Feasibility checks for the canonical MPVRP-CC solution format."""

from __future__ import annotations

from typing import Any

from .schemas import Instance, ParsedSolutionDat
from .utils import solution_node_key


EPSILON = 1e-2
METRIC_TOLERANCE = 0.2


def verify_solution(
    instance: Instance,
    solution: ParsedSolutionDat,
    *,
    check_reported_metrics: bool = False,
) -> tuple[list[str], dict[str, Any]]:
    """Check route feasibility and recompute all performance metrics.

    Values reported in the solution file are informative by default: rounding
    or stale summary values must not invalidate an otherwise feasible route.
    They can still be audited explicitly with ``check_reported_metrics=True``.
    """
    errors: list[str] = []
    vehicles = {int(key[1:]): value for key, value in instance.camions.items()}
    depots = {int(key[1:]): value for key, value in instance.depots.items()}
    stations = {int(key[1:]): value for key, value in instance.stations.items()}

    delivered: dict[tuple[str, int], float] = {}
    loaded: dict[tuple[str, int], float] = {}
    seen_vehicle_visits: set[tuple[int, int, int]] = set()
    seen_vehicle_ids: set[int] = set()
    total_changes = 0
    total_switch_cost = 0.0
    total_distance = 0.0

    for route in solution.vehicles:
        vehicle_id = route.vehicle_id
        if vehicle_id in seen_vehicle_ids:
            errors.append(f"Vehicle {vehicle_id}: duplicate route block")
            continue
        seen_vehicle_ids.add(vehicle_id)

        vehicle = vehicles.get(vehicle_id)
        if vehicle is None:
            errors.append(f"Vehicle {vehicle_id}: missing from instance")
            continue
        if len(route.nodes) != len(route.products):
            errors.append(
                f"Vehicle {vehicle_id}: route/product lengths differ "
                f"({len(route.nodes)} vs {len(route.products)})"
            )
            continue
        keys = [solution_node_key(node["kind"], node["id"]) for node in route.nodes]
        expected_garage = str(vehicle.garage_id)
        if not expected_garage.startswith("G"):
            expected_garage = f"G{expected_garage}"
        if not keys:
            errors.append(f"Vehicle {vehicle_id}: empty route")
            continue
        if keys[0] != expected_garage or keys[-1] != expected_garage:
            errors.append(
                f"Vehicle {vehicle_id}: expected home garage route {expected_garage}...{expected_garage}, "
                f"got {keys[0]}...{keys[-1]}"
            )
        if len(route.nodes) < 4:
            errors.append(f"Vehicle {vehicle_id}: route must contain a garage, depot, station and return garage")
            continue

        for first, second in zip(keys, keys[1:]):
            distance = instance.distances.get((first, second))
            if distance is None:
                errors.append(f"Vehicle {vehicle_id}: unknown arc {first} -> {second}")
            else:
                total_distance += float(distance)

        products = [product for product, _ in route.products]
        cumulative_costs = [cost for _, cost in route.products]
        if any(product < 0 or product >= instance.num_products for product in products):
            errors.append(f"Vehicle {vehicle_id}: product outside [0, {instance.num_products - 1}]")
            continue

        initial_product = int(vehicle.initial_product)
        if products[0] != initial_product:
            errors.append(
                f"Vehicle {vehicle_id}: first product must be initial product {initial_product}, "
                f"got {products[0]}"
            )

        cumulative = 0.0
        current_load: float | None = None
        current_delivered = 0.0
        trip_product: int | None = None
        trip_has_station = False

        for index, (node, product) in enumerate(zip(route.nodes, products)):
            kind = node["kind"]
            node_id = int(node["id"])
            quantity = float(node.get("qty", 0))

            if quantity < -EPSILON:
                errors.append(f"Vehicle {vehicle_id}: negative quantity at {keys[index]}")

            if kind == "garage":
                if index not in (0, len(route.nodes) - 1):
                    errors.append(f"Vehicle {vehicle_id}: garage may only appear at route endpoints")
                if index == len(route.nodes) - 1 and current_load is not None:
                    _close_trip(errors, vehicle_id, current_load, current_delivered, trip_has_station)
                if index > 0 and product != products[index - 1]:
                    errors.append(f"Vehicle {vehicle_id}: product cannot change at a garage")

            elif kind == "depot":
                if node_id not in depots:
                    errors.append(f"Vehicle {vehicle_id}: unknown depot D{node_id}")
                    continue
                if current_load is not None:
                    _close_trip(errors, vehicle_id, current_load, current_delivered, trip_has_station)
                if quantity <= EPSILON:
                    errors.append(f"Vehicle {vehicle_id}: depot D{node_id} load must be positive")
                if quantity > float(vehicle.capacity) + EPSILON:
                    errors.append(
                        f"Vehicle {vehicle_id}: capacity exceeded at D{node_id} "
                        f"({quantity} > {vehicle.capacity})"
                    )
                previous_product = products[index - 1] if index else initial_product
                if product != previous_product:
                    total_changes += 1
                    cumulative += float(instance.costs[(previous_product, product)])
                loaded[(f"D{node_id}", product)] = loaded.get((f"D{node_id}", product), 0.0) + quantity
                current_load = quantity
                current_delivered = 0.0
                trip_product = product
                trip_has_station = False

            elif kind == "station":
                if node_id not in stations:
                    errors.append(f"Vehicle {vehicle_id}: unknown station S{node_id}")
                    continue
                if current_load is None or trip_product is None:
                    errors.append(f"Vehicle {vehicle_id}: station S{node_id} visited before loading at a depot")
                    continue
                if product != trip_product:
                    errors.append(f"Vehicle {vehicle_id}: product changed inside a mini-route at S{node_id}")
                if quantity <= EPSILON:
                    errors.append(f"Vehicle {vehicle_id}: delivery at S{node_id} must be positive")
                visit = (vehicle_id, node_id, product)
                if visit in seen_vehicle_visits:
                    errors.append(
                        f"Vehicle {vehicle_id}: station S{node_id}, product {product} visited more than once"
                    )
                seen_vehicle_visits.add(visit)
                station_key = f"S{node_id}"
                delivered[(station_key, product)] = delivered.get((station_key, product), 0.0) + quantity
                current_delivered += quantity
                trip_has_station = True

            expected_cumulative = float(cumulative_costs[index])
            if check_reported_metrics and abs(expected_cumulative - cumulative) > METRIC_TOLERANCE:
                errors.append(
                    f"Vehicle {vehicle_id}: cumulative changeover cost at step {index + 1} "
                    f"is {expected_cumulative}, expected {cumulative:.2f}"
                )

        total_switch_cost += cumulative

    for station in instance.stations.values():
        for product, demand in station.demand.items():
            actual = delivered.get((station.id, product), 0.0)
            if abs(actual - float(demand)) > EPSILON:
                errors.append(
                    f"Unsatisfied demand: {station.id} product {product} "
                    f"(demand={demand}, delivered={actual})"
                )

    for depot in instance.depots.values():
        for product, stock in depot.stocks.items():
            actual = loaded.get((depot.id, product), 0.0)
            if actual > float(stock) + EPSILON:
                errors.append(
                    f"Stock exceeded: {depot.id} product {product} "
                    f"(stock={stock}, withdrawn={actual})"
                )

    computed = {
        "used_vehicles": len(seen_vehicle_ids),
        "total_changes": total_changes,
        "total_switch_cost": total_switch_cost,
        "distance_total": total_distance,
    }
    if check_reported_metrics:
        _check_metric(errors, solution.metrics, computed, "used_vehicles", 0)
        _check_metric(errors, solution.metrics, computed, "total_changes", 0)
        _check_metric(errors, solution.metrics, computed, "total_switch_cost", METRIC_TOLERANCE)
        _check_metric(errors, solution.metrics, computed, "distance_total", METRIC_TOLERANCE)
    return errors, computed


def _close_trip(
    errors: list[str], vehicle_id: int, loaded: float, delivered: float, has_station: bool
) -> None:
    if not has_station:
        errors.append(f"Vehicle {vehicle_id}: every depot load must be followed by at least one delivery")
    if abs(loaded - delivered) > EPSILON:
        errors.append(
            f"Vehicle {vehicle_id}: mass conservation violated "
            f"(loaded={loaded}, delivered={delivered})"
        )


def _check_metric(
    errors: list[str], submitted: dict[str, Any], computed: dict[str, Any], key: str, tolerance: float
) -> None:
    actual = submitted.get(key)
    expected = computed[key]
    if actual is None or abs(float(actual) - float(expected)) > tolerance:
        errors.append(f"{key} metric inconsistent: file={actual}, computed={expected:.2f}")
