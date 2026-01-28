import os
import re
import tempfile

import pytest
import numpy as np

from backup.core.generator.instance_provider import (
    generer_instance,
    validate_instance,
    get_existing_instance_ids,
)


class TestGenerateInstance:
    """Test suite for generer_instance function."""

    def test_generate_basic_instance(self, temp_dir, instance_generation_params):
        """Test generating a basic valid instance."""
        params = instance_generation_params.copy()
        params["output_dir"] = temp_dir
        
        filepath = generer_instance(**params)
        
        assert filepath is not None
        assert os.path.exists(filepath)
        assert filepath.endswith(".dat")

    def test_generate_instance_filename_format(self, temp_dir, instance_generation_params):
        """Test that generated filename follows the expected format."""
        params = instance_generation_params.copy()
        params["output_dir"] = temp_dir
        
        filepath = generer_instance(**params)
        filename = os.path.basename(filepath)
        
        # Expected format: MPVRP_{id}_s{stations}_d{depots}_p{products}.dat
        pattern = r'^MPVRP_(.+)_s(\d+)_d(\d+)_p(\d+)\.dat$'
        match = re.match(pattern, filename)
        
        assert match is not None
        assert match.group(1) == params["id_inst"]
        assert int(match.group(2)) == params["nb_s"]
        assert int(match.group(3)) == params["nb_d"]
        assert int(match.group(4)) == params["nb_p"]

    def test_generate_instance_with_seed(self, temp_dir, instance_generation_params):
        """Test that using the same seed produces identical instances."""
        params = instance_generation_params.copy()
        params["output_dir"] = temp_dir
        params["seed"] = 12345
        
        # Generate first instance
        filepath1 = generer_instance(**params)
        with open(filepath1, 'r') as f:
            content1 = f.read()
        
        # Remove first instance and regenerate
        os.remove(filepath1)
        filepath2 = generer_instance(**params)
        with open(filepath2, 'r') as f:
            content2 = f.read()
        
        # Contents should be identical (except possibly UUID)
        lines1 = [l for l in content1.split('\n') if not l.startswith('#')]
        lines2 = [l for l in content2.split('\n') if not l.startswith('#')]
        assert lines1 == lines2

    def test_generate_instance_different_seeds(self, temp_dir, instance_generation_params):
        """Test that different seeds produce different instances."""
        params1 = instance_generation_params.copy()
        params1["output_dir"] = temp_dir
        params1["seed"] = 111
        params1["id_inst"] = "SEED1"
        
        params2 = instance_generation_params.copy()
        params2["output_dir"] = temp_dir
        params2["seed"] = 222
        params2["id_inst"] = "SEED2"
        
        filepath1 = generer_instance(**params1)
        filepath2 = generer_instance(**params2)
        
        with open(filepath1, 'r') as f:
            content1 = f.read()
        with open(filepath2, 'r') as f:
            content2 = f.read()
        
        # Remove headers and UUIDs for comparison
        lines1 = [l for l in content1.split('\n') if l and not l.startswith('#')]
        lines2 = [l for l in content2.split('\n') if l and not l.startswith('#')]
        
        # At least some data lines should differ (not the first param line though)
        assert lines1[1:] != lines2[1:]  # Skip param line, compare the rest

    def test_generate_instance_force_overwrite(self, temp_dir, instance_generation_params):
        """Test force overwrite functionality."""
        params = instance_generation_params.copy()
        params["output_dir"] = temp_dir
        params["force_overwrite"] = True
        
        # Generate twice with force_overwrite
        filepath1 = generer_instance(**params)
        filepath2 = generer_instance(**params)
        
        assert filepath1 == filepath2
        assert os.path.exists(filepath2)

    def test_generate_instance_min_params(self, temp_dir):
        """Test generating instance with minimum parameters."""
        filepath = generer_instance(
            id_inst="MIN01",
            nb_v=1,
            nb_d=1,
            nb_g=1,
            nb_s=1,
            nb_p=1,
            seed=42,
            force_overwrite=True,
            output_dir=temp_dir,
            silent=True
        )
        
        assert filepath is not None
        assert os.path.exists(filepath)

    def test_generate_instance_large_params(self, temp_dir):
        """Test generating instance with larger parameters."""
        filepath = generer_instance(
            id_inst="LARGE01",
            nb_v=5,
            nb_d=3,
            nb_g=2,
            nb_s=10,
            nb_p=4,
            max_coord=200.0,
            min_capacite=5000,
            max_capacite=20000,
            seed=42,
            force_overwrite=True,
            output_dir=temp_dir,
            silent=True
        )
        
        assert filepath is not None
        assert os.path.exists(filepath)

    @pytest.mark.parametrize("nb_products", [1, 2, 5, 10])
    def test_generate_instance_various_products(self, temp_dir, nb_products):
        """Test generating instances with various numbers of products."""
        filepath = generer_instance(
            id_inst=f"PROD{nb_products}",
            nb_v=2,
            nb_d=1,
            nb_g=1,
            nb_s=3,
            nb_p=nb_products,
            seed=42,
            force_overwrite=True,
            output_dir=temp_dir,
            silent=True
        )
        
        assert filepath is not None
        
        # Verify the file contains correct number of products
        with open(filepath, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith('#')]
        
        params = [int(x) for x in lines[0].split()]
        assert params[0] == nb_products

    @pytest.mark.parametrize("nb_vehicles", [1, 3, 5, 10])
    def test_generate_instance_various_vehicles(self, temp_dir, nb_vehicles):
        """Test generating instances with various numbers of vehicles."""
        filepath = generer_instance(
            id_inst=f"VEH{nb_vehicles}",
            nb_v=nb_vehicles,
            nb_d=1,
            nb_g=1,
            nb_s=5,
            nb_p=2,
            seed=42,
            force_overwrite=True,
            output_dir=temp_dir,
            silent=True
        )
        
        assert filepath is not None


class TestValidateInstance:
    """Test suite for validate_instance function."""

    def test_validate_valid_instance(self):
        """Test validation of a valid instance."""
        nb_p = 2
        params = np.array([nb_p, 1, 1, 2, 2])
        
        vehicles = np.array([
            [1, 5000, 1, 1],
            [2, 5000, 1, 2]
        ])
        
        depots = np.array([
            [1, 50.0, 50.0, 3000, 2000]
        ])
        
        garages = np.array([
            [1, 0.0, 0.0]
        ])
        
        stations = np.array([
            [1, 25.0, 25.0, 1000, 500],
            [2, 75.0, 75.0, 500, 1000]
        ])
        
        transition_costs = np.array([
            [0.0, 10.0],
            [10.0, 0.0]
        ])
        
        errors, warnings = validate_instance(
            params, vehicles, depots, garages, stations, transition_costs, nb_p
        )
        
        assert len(errors) == 0

    def test_validate_insufficient_stock(self):
        """Test validation detects insufficient stock."""
        nb_p = 2
        params = np.array([nb_p, 1, 1, 2, 1])
        
        vehicles = np.array([[1, 5000, 1, 1]])
        
        # Stock is less than demand
        depots = np.array([[1, 50.0, 50.0, 100, 100]])  # Low stock
        
        garages = np.array([[1, 0.0, 0.0]])
        
        stations = np.array([
            [1, 25.0, 25.0, 5000, 5000],  # High demand
            [2, 75.0, 75.0, 5000, 5000]
        ])
        
        transition_costs = np.array([[0.0, 10.0], [10.0, 0.0]])
        
        errors, warnings = validate_instance(
            params, vehicles, depots, garages, stations, transition_costs, nb_p
        )
        
        # Should have errors about insufficient stock
        assert len(errors) > 0
        assert any("Stock" in e for e in errors)

    def test_validate_invalid_garage_reference(self):
        """Test validation detects invalid garage reference."""
        nb_p = 2
        params = np.array([nb_p, 1, 1, 1, 1])
        
        # Vehicle references garage 2, but only garage 1 exists
        vehicles = np.array([[1, 5000, 2, 1]])  # Invalid garage reference
        
        depots = np.array([[1, 50.0, 50.0, 3000, 2000]])
        garages = np.array([[1, 0.0, 0.0]])
        stations = np.array([[1, 25.0, 25.0, 1000, 500]])
        transition_costs = np.array([[0.0, 10.0], [10.0, 0.0]])
        
        errors, warnings = validate_instance(
            params, vehicles, depots, garages, stations, transition_costs, nb_p
        )
        
        assert len(errors) > 0
        assert any("garage" in e.lower() for e in errors)

    def test_validate_invalid_initial_product(self):
        """Test validation detects invalid initial product."""
        nb_p = 2
        params = np.array([nb_p, 1, 1, 1, 1])
        
        # Vehicle has initial product 5, but only products 1-2 exist
        vehicles = np.array([[1, 5000, 1, 5]])  # Invalid product
        
        depots = np.array([[1, 50.0, 50.0, 3000, 2000]])
        garages = np.array([[1, 0.0, 0.0]])
        stations = np.array([[1, 25.0, 25.0, 1000, 500]])
        transition_costs = np.array([[0.0, 10.0], [10.0, 0.0]])
        
        errors, warnings = validate_instance(
            params, vehicles, depots, garages, stations, transition_costs, nb_p
        )
        
        assert len(errors) > 0
        assert any("produit" in e.lower() for e in errors)

    def test_validate_nonzero_diagonal(self):
        """Test validation detects non-zero diagonal in transition matrix."""
        nb_p = 2
        params = np.array([nb_p, 1, 1, 1, 1])
        
        vehicles = np.array([[1, 5000, 1, 1]])
        depots = np.array([[1, 50.0, 50.0, 3000, 2000]])
        garages = np.array([[1, 0.0, 0.0]])
        stations = np.array([[1, 25.0, 25.0, 1000, 500]])
        
        # Non-zero diagonal
        transition_costs = np.array([[5.0, 10.0], [10.0, 5.0]])
        
        errors, warnings = validate_instance(
            params, vehicles, depots, garages, stations, transition_costs, nb_p
        )
        
        assert len(errors) > 0
        assert any("diagonale" in e.lower() for e in errors)

    def test_validate_station_without_demand(self):
        """Test validation detects station with no demand."""
        nb_p = 2
        params = np.array([nb_p, 1, 1, 1, 1])
        
        vehicles = np.array([[1, 5000, 1, 1]])
        depots = np.array([[1, 50.0, 50.0, 3000, 2000]])
        garages = np.array([[1, 0.0, 0.0]])
        
        # Station with zero demand for all products
        stations = np.array([[1, 25.0, 25.0, 0, 0]])
        
        transition_costs = np.array([[0.0, 10.0], [10.0, 0.0]])
        
        errors, warnings = validate_instance(
            params, vehicles, depots, garages, stations, transition_costs, nb_p
        )
        
        assert len(errors) > 0
        assert any("demande" in e.lower() for e in errors)


class TestGetExistingInstanceIds:
    """Test suite for get_existing_instance_ids function."""

    def test_empty_directory(self, temp_dir):
        """Test getting IDs from empty directory."""
        ids = get_existing_instance_ids(temp_dir)
        assert ids == set()

    def test_nonexistent_directory(self):
        """Test getting IDs from non-existent directory."""
        ids = get_existing_instance_ids("/nonexistent/path")
        assert ids == set()

    def test_directory_with_instances(self, temp_dir):
        """Test getting IDs from directory with instance files."""
        # Create some instance files
        filenames = [
            "MPVRP_01_s5_d2_p2.dat",
            "MPVRP_02_s10_d3_p4.dat",
            "MPVRP_TEST_s8_d2_p3.dat",
        ]
        
        for fname in filenames:
            filepath = os.path.join(temp_dir, fname)
            with open(filepath, 'w') as f:
                f.write("dummy content")
        
        ids = get_existing_instance_ids(temp_dir)
        
        assert "01" in ids
        assert "02" in ids
        assert "TEST" in ids

    def test_ignores_non_instance_files(self, temp_dir):
        """Test that non-instance files are ignored."""
        # Create instance file and non-instance file
        instance_file = os.path.join(temp_dir, "MPVRP_01_s5_d2_p2.dat")
        other_file = os.path.join(temp_dir, "readme.txt")
        
        with open(instance_file, 'w') as f:
            f.write("dummy")
        with open(other_file, 'w') as f:
            f.write("readme")
        
        ids = get_existing_instance_ids(temp_dir)
        
        assert "01" in ids
        assert len(ids) == 1


class TestInstanceFileStructure:
    """Test suite for verifying the structure of generated instance files."""

    def test_instance_file_has_uuid(self, temp_dir, instance_generation_params):
        """Test that generated instance has a UUID comment."""
        params = instance_generation_params.copy()
        params["output_dir"] = temp_dir
        
        filepath = generer_instance(**params)
        
        with open(filepath, 'r') as f:
            first_line = f.readline().strip()
        
        # First line should be a UUID comment
        assert first_line.startswith('#')
        uuid_pattern = r'^#\s*[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        assert re.match(uuid_pattern, first_line, re.IGNORECASE)

    def test_instance_file_params_line(self, temp_dir, instance_generation_params):
        """Test that the parameters line is correctly formatted."""
        params = instance_generation_params.copy()
        params["output_dir"] = temp_dir
        
        filepath = generer_instance(**params)
        
        with open(filepath, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith('#')]
        
        # First non-comment line should be parameters
        param_line = lines[0].split()
        assert len(param_line) == 5  # nb_p, nb_d, nb_g, nb_s, nb_v
        
        # Verify parameter values
        nb_p, nb_d, nb_g, nb_s, nb_v = [int(x) for x in param_line]
        assert nb_p == params["nb_p"]
        assert nb_d == params["nb_d"]
        assert nb_g == params["nb_g"]
        assert nb_s == params["nb_s"]
        assert nb_v == params["nb_v"]

    def test_instance_file_transition_matrix(self, temp_dir, instance_generation_params):
        """Test that transition matrix has correct dimensions."""
        params = instance_generation_params.copy()
        params["output_dir"] = temp_dir
        
        filepath = generer_instance(**params)
        
        with open(filepath, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith('#')]
        
        nb_p = int(lines[0].split()[0])
        
        # Lines 1 to nb_p should be the transition matrix
        for i in range(1, nb_p + 1):
            costs = lines[i].split()
            assert len(costs) == nb_p, f"Row {i} of transition matrix has wrong length"

    def test_instance_file_line_count(self, temp_dir, instance_generation_params):
        """Test that instance file has correct number of lines."""
        params = instance_generation_params.copy()
        params["output_dir"] = temp_dir
        
        filepath = generer_instance(**params)
        
        with open(filepath, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith('#')]
        
        nb_p = params["nb_p"]
        nb_v = params["nb_v"]
        nb_d = params["nb_d"]
        nb_g = params["nb_g"]
        nb_s = params["nb_s"]
        
        expected_lines = 1 + nb_p + nb_v + nb_d + nb_g + nb_s
        assert len(lines) == expected_lines
