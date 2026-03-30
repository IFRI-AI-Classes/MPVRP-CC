import pytest

from backup.core.model.schemas import (
    Camion, Depot, Garage, Station, Instance,
    ParsedSolutionVehicle, ParsedSolutionDat
)


class TestCamion:
    """Test suite for Camion (vehicle) dataclass."""

    def test_camion_creation(self):
        """Test basic Camion creation."""
        camion = Camion(
            id="K1",
            capacity=10000.0,
            garage_id=1,
            initial_product=1
        )
        assert camion.id == "K1"
        assert camion.capacity == 10000.0
        assert camion.garage_id == 1
        assert camion.initial_product == 1

    def test_camion_with_different_capacities(self):
        """Test Camion with various capacity values."""
        capacities = [1000, 5000, 10000, 25000, 50000]
        for cap in capacities:
            camion = Camion(id="K1", capacity=cap, garage_id=1, initial_product=1)
            assert camion.capacity == cap

    def test_camion_with_different_products(self):
        """Test Camion with various initial product values."""
        for product in range(1, 6):
            camion = Camion(id="K1", capacity=10000, garage_id=1, initial_product=product)
            assert camion.initial_product == product


class TestDepot:
    """Test suite for Depot dataclass."""

    def test_depot_creation(self):
        """Test basic Depot creation."""
        depot = Depot(
            id="D1",
            location=(50.0, 50.0),
            stocks={0: 5000, 1: 3000}
        )
        assert depot.id == "D1"
        assert depot.location == (50.0, 50.0)
        assert depot.stocks[0] == 5000
        assert depot.stocks[1] == 3000

    def test_depot_with_multiple_products(self):
        """Test Depot with various numbers of products."""
        num_products = 5
        stocks = {i: 1000 * (i + 1) for i in range(num_products)}
        depot = Depot(id="D1", location=(10.0, 20.0), stocks=stocks)
        
        assert len(depot.stocks) == num_products
        for i in range(num_products):
            assert depot.stocks[i] == 1000 * (i + 1)

    def test_depot_location_coordinates(self):
        """Test Depot with various location coordinates."""
        locations = [(0.0, 0.0), (100.0, 100.0), (50.5, 25.3), (-10.0, 20.0)]
        for loc in locations:
            depot = Depot(id="D1", location=loc, stocks={0: 1000})
            assert depot.location == loc


class TestGarage:
    """Test suite for Garage dataclass."""

    def test_garage_creation(self):
        """Test basic Garage creation."""
        garage = Garage(id="G1", location=(0.0, 0.0))
        assert garage.id == "G1"
        assert garage.location == (0.0, 0.0)

    def test_garage_with_various_locations(self):
        """Test Garage with different locations."""
        locations = [(0.0, 0.0), (50.0, 50.0), (99.9, 1.1)]
        for i, loc in enumerate(locations, 1):
            garage = Garage(id=f"G{i}", location=loc)
            assert garage.id == f"G{i}"
            assert garage.location == loc


class TestStation:
    """Test suite for Station dataclass."""

    def test_station_creation(self):
        """Test basic Station creation."""
        station = Station(
            id="S1",
            location=(25.0, 25.0),
            demand={0: 1000, 1: 500}
        )
        assert station.id == "S1"
        assert station.location == (25.0, 25.0)
        assert station.demand[0] == 1000
        assert station.demand[1] == 500

    def test_station_with_zero_demand(self):
        """Test Station where some products have zero demand."""
        station = Station(
            id="S1",
            location=(10.0, 10.0),
            demand={0: 1000, 1: 0, 2: 500}
        )
        assert station.demand[1] == 0

    def test_station_with_multiple_products(self):
        """Test Station with many products."""
        num_products = 10
        demand = {i: 100 * (i + 1) for i in range(num_products)}
        station = Station(id="S1", location=(50.0, 50.0), demand=demand)
        
        assert len(station.demand) == num_products


class TestInstance:
    """Test suite for Instance dataclass."""

    def test_instance_creation(self, sample_instance):
        """Test basic Instance creation using fixture."""
        assert sample_instance.num_products == 2
        assert sample_instance.num_camions == 1
        assert sample_instance.num_depots == 1
        assert sample_instance.num_garages == 1
        assert sample_instance.num_stations == 1

    def test_instance_camions_access(self, sample_instance):
        """Test accessing camions from Instance."""
        assert "K1" in sample_instance.camions
        camion = sample_instance.camions["K1"]
        assert camion.capacity == 10000.0

    def test_instance_costs_access(self, sample_instance):
        """Test accessing transition costs from Instance."""
        assert sample_instance.costs[(0, 0)] == 0.0
        assert sample_instance.costs[(0, 1)] == 10.0

    def test_instance_empty_distances(self, sample_instance):
        """Test that distances dict can be empty initially."""
        assert sample_instance.distances == {}


class TestParsedSolutionVehicle:
    """Test suite for ParsedSolutionVehicle dataclass."""

    def test_solution_vehicle_creation(self, sample_solution_vehicle):
        """Test basic ParsedSolutionVehicle creation."""
        assert sample_solution_vehicle.vehicle_id == 1
        assert len(sample_solution_vehicle.nodes) == 4
        assert len(sample_solution_vehicle.products) == 4

    def test_solution_vehicle_nodes_structure(self, sample_solution_vehicle):
        """Test the structure of nodes in solution vehicle."""
        nodes = sample_solution_vehicle.nodes
        
        # First node should be garage
        assert nodes[0]["kind"] == "garage"
        
        # Second node should be depot
        assert nodes[1]["kind"] == "depot"
        
        # Third node should be station
        assert nodes[2]["kind"] == "station"
        
        # Last node should be garage
        assert nodes[-1]["kind"] == "garage"

    def test_solution_vehicle_frozen(self):
        """Test that ParsedSolutionVehicle is immutable (frozen)."""
        vehicle = ParsedSolutionVehicle(
            vehicle_id=1,
            nodes=[{"kind": "garage", "id": 1, "qty": 0}],
            products=[(0, 0.0)]
        )
        with pytest.raises(AttributeError):
            vehicle.vehicle_id = 2


class TestParsedSolutionDat:
    """Test suite for ParsedSolutionDat dataclass."""

    def test_solution_dat_creation(self, sample_solution):
        """Test basic ParsedSolutionDat creation."""
        assert len(sample_solution.vehicles) == 1
        assert sample_solution.metrics["used_vehicles"] == 1

    def test_solution_dat_metrics(self, sample_solution):
        """Test metrics in ParsedSolutionDat."""
        metrics = sample_solution.metrics
        assert "used_vehicles" in metrics
        assert "total_changes" in metrics
        assert "total_switch_cost" in metrics
        assert "distance_total" in metrics

    def test_solution_dat_frozen(self, sample_solution_vehicle):
        """Test that ParsedSolutionDat is immutable (frozen)."""
        solution = ParsedSolutionDat(
            vehicles=[sample_solution_vehicle],
            metrics={"used_vehicles": 1}
        )
        with pytest.raises(AttributeError):
            solution.vehicles = []
