"""
Unit tests for MPVRP-CC utility functions.

Tests the utility functions in backup.core.model.utils:
- euclidean_distance
- parse_instance
- compute_distances
- _parse_solution_route_token
- _parse_solution_product_token
- solution_node_key
- parse_solution
"""
import os
import math
import pytest
import tempfile

from backup.core.model.utils import (
    euclidean_distance,
    parse_instance,
    compute_distances,
    _parse_solution_route_token,
    _parse_solution_product_token,
    solution_node_key,
    parse_solution,
)
from backup.core.model.schemas import Instance


class TestEuclideanDistance:
    """Test suite for euclidean_distance function."""

    def test_same_point(self):
        """Test distance between identical points is zero."""
        point = (10.0, 20.0)
        assert euclidean_distance(point, point) == 0.0

    def test_horizontal_distance(self):
        """Test distance along horizontal axis."""
        p1 = (0.0, 0.0)
        p2 = (10.0, 0.0)
        assert euclidean_distance(p1, p2) == 10.0

    def test_vertical_distance(self):
        """Test distance along vertical axis."""
        p1 = (0.0, 0.0)
        p2 = (0.0, 10.0)
        assert euclidean_distance(p1, p2) == 10.0

    def test_diagonal_distance(self):
        """Test distance along diagonal (3-4-5 triangle)."""
        p1 = (0.0, 0.0)
        p2 = (3.0, 4.0)
        assert euclidean_distance(p1, p2) == 5.0

    def test_negative_coordinates(self):
        """Test distance with negative coordinates."""
        p1 = (-5.0, -5.0)
        p2 = (5.0, 5.0)
        expected = math.sqrt(200)  # sqrt((10)^2 + (10)^2)
        assert abs(euclidean_distance(p1, p2) - expected) < 1e-10

    def test_floating_point_coordinates(self):
        """Test distance with floating point coordinates."""
        p1 = (1.5, 2.5)
        p2 = (4.5, 6.5)
        expected = math.sqrt((3.0)**2 + (4.0)**2)
        assert abs(euclidean_distance(p1, p2) - expected) < 1e-10

    def test_symmetry(self):
        """Test that distance is symmetric."""
        p1 = (1.0, 2.0)
        p2 = (5.0, 7.0)
        assert euclidean_distance(p1, p2) == euclidean_distance(p2, p1)


class TestParseInstance:
    """Test suite for parse_instance function."""

    def test_parse_valid_instance(self, sample_instance_file):
        """Test parsing a valid instance file."""
        instance = parse_instance(sample_instance_file)
        
        assert isinstance(instance, Instance)
        assert instance.num_products == 2
        assert instance.num_depots == 1
        assert instance.num_garages == 1
        assert instance.num_stations == 2
        assert instance.num_camions == 1

    def test_parse_instance_camions(self, sample_instance_file):
        """Test that camions are parsed correctly."""
        instance = parse_instance(sample_instance_file)
        
        assert "K1" in instance.camions
        camion = instance.camions["K1"]
        assert camion.capacity == 5000.0
        assert camion.garage_id == "G1"

    def test_parse_instance_depots(self, sample_instance_file):
        """Test that depots are parsed correctly."""
        instance = parse_instance(sample_instance_file)
        
        assert "D1" in instance.depots
        depot = instance.depots["D1"]
        assert depot.location == (50.0, 50.0)
        assert depot.stocks[0] == 3000
        assert depot.stocks[1] == 2000

    def test_parse_instance_garages(self, sample_instance_file):
        """Test that garages are parsed correctly."""
        instance = parse_instance(sample_instance_file)
        
        assert "G1" in instance.garages
        garage = instance.garages["G1"]
        assert garage.location == (0.0, 0.0)

    def test_parse_instance_stations(self, sample_instance_file):
        """Test that stations are parsed correctly."""
        instance = parse_instance(sample_instance_file)
        
        assert "S1" in instance.stations
        assert "S2" in instance.stations
        
        station1 = instance.stations["S1"]
        assert station1.demand[0] == 1000
        assert station1.demand[1] == 500

    def test_parse_instance_costs(self, sample_instance_file):
        """Test that transition costs are parsed correctly."""
        instance = parse_instance(sample_instance_file)
        
        # Diagonal should be 0
        assert instance.costs[(0, 0)] == 0.0
        assert instance.costs[(1, 1)] == 0.0
        # Off-diagonal values
        assert instance.costs[(0, 1)] == 15.0
        assert instance.costs[(1, 0)] == 15.0

    def test_parse_instance_distances_computed(self, sample_instance_file):
        """Test that distances are computed after parsing."""
        instance = parse_instance(sample_instance_file)
        
        # Distances should be populated
        assert len(instance.distances) > 0
        # Check some specific distances exist
        assert ("G1", "D1") in instance.distances
        assert ("D1", "S1") in instance.distances

    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            parse_instance("/nonexistent/path/file.dat")

    def test_parse_invalid_file(self, invalid_instance_file):
        """Test parsing an invalid instance file."""
        with pytest.raises(RuntimeError):
            parse_instance(invalid_instance_file)


class TestComputeDistances:
    """Test suite for compute_distances function."""

    def test_compute_distances_basic(self, sample_instance):
        """Test basic distance computation."""
        # Add locations to sample instance
        sample_instance.garages["G1"].location = (0.0, 0.0)
        sample_instance.depots["D1"].location = (50.0, 50.0)
        sample_instance.stations["S1"].location = (25.0, 25.0)
        
        distances = compute_distances(sample_instance)
        
        # Should have distances between all pairs
        assert ("G1", "D1") in distances
        assert ("G1", "S1") in distances
        assert ("D1", "S1") in distances

    def test_compute_distances_symmetry(self, sample_instance):
        """Test that computed distances are symmetric."""
        sample_instance.garages["G1"].location = (0.0, 0.0)
        sample_instance.depots["D1"].location = (50.0, 50.0)
        
        distances = compute_distances(sample_instance)
        
        assert distances[("G1", "D1")] == distances[("D1", "G1")]

    def test_compute_distances_self_zero(self, sample_instance):
        """Test that distance from a node to itself is zero."""
        distances = compute_distances(sample_instance)
        
        for node_id in ["G1", "D1", "S1"]:
            if (node_id, node_id) in distances:
                assert distances[(node_id, node_id)] == 0.0


class TestParseSolutionRouteToken:
    """Test suite for _parse_solution_route_token function."""

    def test_parse_depot_token(self):
        """Test parsing depot token format: id[qty]"""
        result = _parse_solution_route_token("1[500]")
        
        assert result["kind"] == "depot"
        assert result["id"] == 1
        assert result["qty"] == 500

    def test_parse_station_token(self):
        """Test parsing station token format: id(qty)"""
        result = _parse_solution_route_token("5(300)")
        
        assert result["kind"] == "station"
        assert result["id"] == 5
        assert result["qty"] == 300

    def test_parse_garage_token(self):
        """Test parsing garage token format: id"""
        result = _parse_solution_route_token("2")
        
        assert result["kind"] == "garage"
        assert result["id"] == 2
        assert result["qty"] == 0

    def test_parse_token_with_whitespace(self):
        """Test parsing tokens with leading/trailing whitespace."""
        result = _parse_solution_route_token("  1[500]  ")
        
        assert result["kind"] == "depot"
        assert result["id"] == 1

    def test_parse_empty_token_raises(self):
        """Test that empty token raises ValueError."""
        with pytest.raises(ValueError, match="Empty token"):
            _parse_solution_route_token("")

    def test_parse_large_quantities(self):
        """Test parsing tokens with large quantities."""
        result = _parse_solution_route_token("1[99999]")
        assert result["qty"] == 99999
        
        result = _parse_solution_route_token("1(99999)")
        assert result["qty"] == 99999


class TestParseSolutionProductToken:
    """Test suite for _parse_solution_product_token function."""

    def test_parse_product_token(self):
        """Test parsing product token format: p(cost)"""
        product, cost = _parse_solution_product_token("2(150.5)")
        
        assert product == 2
        assert cost == 150.5

    def test_parse_zero_cost(self):
        """Test parsing product with zero cost."""
        product, cost = _parse_solution_product_token("0(0.0)")
        
        assert product == 0
        assert cost == 0.0

    def test_parse_token_with_whitespace(self):
        """Test parsing tokens with whitespace."""
        product, cost = _parse_solution_product_token("  1(50.0)  ")
        
        assert product == 1
        assert cost == 50.0

    def test_parse_empty_token_raises(self):
        """Test that empty token raises ValueError."""
        with pytest.raises(ValueError, match="Empty token"):
            _parse_solution_product_token("")

    def test_parse_invalid_format_raises(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid product token"):
            _parse_solution_product_token("invalid")


class TestSolutionNodeKey:
    """Test suite for solution_node_key function."""

    def test_garage_key(self):
        """Test garage key generation."""
        assert solution_node_key("garage", 1) == "G1"
        assert solution_node_key("garage", 5) == "G5"

    def test_depot_key(self):
        """Test depot key generation."""
        assert solution_node_key("depot", 1) == "D1"
        assert solution_node_key("depot", 3) == "D3"

    def test_station_key(self):
        """Test station key generation."""
        assert solution_node_key("station", 1) == "S1"
        assert solution_node_key("station", 10) == "S10"

    def test_unknown_kind_raises(self):
        """Test that unknown kind raises ValueError."""
        with pytest.raises(ValueError, match="Unknown kind"):
            solution_node_key("unknown", 1)


class TestParseSolution:
    """Test suite for parse_solution function."""

    def test_parse_valid_solution(self, sample_solution_file):
        """Test parsing a valid solution file."""
        solution = parse_solution(sample_solution_file)
        
        assert len(solution.vehicles) == 1
        assert solution.metrics["used_vehicles"] == 1

    def test_parse_solution_metrics(self, sample_solution_file):
        """Test that all metrics are parsed correctly."""
        solution = parse_solution(sample_solution_file)
        
        assert "used_vehicles" in solution.metrics
        assert "total_changes" in solution.metrics
        assert "total_switch_cost" in solution.metrics
        assert "distance_total" in solution.metrics
        assert "processor" in solution.metrics
        assert "time" in solution.metrics

    def test_parse_solution_vehicle_route(self, sample_solution_file):
        """Test that vehicle route is parsed correctly."""
        solution = parse_solution(sample_solution_file)
        
        vehicle = solution.vehicles[0]
        assert vehicle.vehicle_id == 1
        assert len(vehicle.nodes) > 0
        assert len(vehicle.products) > 0
        assert len(vehicle.nodes) == len(vehicle.products)

    def test_parse_nonexistent_solution(self):
        """Test parsing a solution file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            parse_solution("/nonexistent/path/solution.dat")

    def test_parse_solution_with_multiple_vehicles(self, temp_dir):
        """Test parsing solution with multiple vehicles."""
        filepath = os.path.join(temp_dir, "multi_vehicle_solution.dat")
        content = """1: 1 - 1 [1000] - 1 (1000) - 1
1: 0(0.0) - 0(0.0) - 0(0.0) - 0(0.0)

2: 1 - 1 [500] - 2 (500) - 1
2: 0(0.0) - 0(0.0) - 0(0.0) - 0(0.0)

2
0
0.00
200.00
test
2.000
"""
        with open(filepath, 'w') as f:
            f.write(content)
        
        solution = parse_solution(filepath)
        
        assert len(solution.vehicles) == 2
        assert solution.metrics["used_vehicles"] == 2
