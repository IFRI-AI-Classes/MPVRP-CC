"""
Integration tests for end-to-end workflows.

Tests complete workflows from instance generation to solution verification.
"""
import os
import tempfile
import pytest

pytestmark = pytest.mark.integration


class TestGenerateAndVerifyWorkflow:
    """Test complete generate-and-verify workflow."""

    def test_generate_then_parse_instance(self, temp_dir, instance_generation_params):
        """Test generating an instance and then parsing it."""
        from backup.core.generator.instance_provider import generer_instance
        from backup.core.model.utils import parse_instance
        
        # Generate instance
        params = instance_generation_params.copy()
        params["output_dir"] = temp_dir
        
        filepath = generer_instance(**params)
        assert filepath is not None
        
        # Parse the generated instance
        instance = parse_instance(filepath)
        
        # Verify parsed data matches generation params
        assert instance.num_products == params["nb_p"]
        assert instance.num_camions == params["nb_v"]
        assert instance.num_depots == params["nb_d"]
        assert instance.num_garages == params["nb_g"]
        assert instance.num_stations == params["nb_s"]

    def test_generate_then_verify_instance(self, temp_dir, instance_generation_params):
        """Test generating an instance and verifying its structure."""
        from backup.core.generator.instance_provider import generer_instance
        from backup.core.generator.instance_verificator import InstanceVerificator
        import io
        import sys
        
        # Generate instance
        params = instance_generation_params.copy()
        params["output_dir"] = temp_dir
        
        filepath = generer_instance(**params)
        assert filepath is not None
        
        # Verify the generated instance
        verificator = InstanceVerificator(filepath)
        
        # Suppress stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            is_valid = verificator.verify()
        finally:
            sys.stdout = old_stdout
        
        assert is_valid, f"Generated instance failed verification: {verificator.errors}"


class TestBatchGeneration:
    """Test batch generation capabilities."""

    @pytest.mark.slow
    def test_generate_multiple_instances(self, temp_dir):
        """Test generating multiple instances."""
        from backup.core.generator.instance_provider import generer_instance
        
        num_instances = 3
        generated_files = []
        
        for i in range(num_instances):
            filepath = generer_instance(
                id_inst=f"BATCH{i:02d}",
                nb_v=2,
                nb_d=1,
                nb_g=1,
                nb_s=3,
                nb_p=2,
                seed=i,
                force_overwrite=True,
                output_dir=temp_dir,
                silent=True
            )
            generated_files.append(filepath)
        
        # All files should exist
        for filepath in generated_files:
            assert filepath is not None
            assert os.path.exists(filepath)
        
        # All files should be different
        contents = []
        for filepath in generated_files:
            with open(filepath, 'r') as f:
                # Skip UUID line for comparison
                lines = [l for l in f.readlines() if not l.startswith('#')]
                contents.append(''.join(lines))
        
        # At least some should be different due to different seeds
        assert len(set(contents)) > 1


class TestRealInstanceFiles:
    """Test using real instance files from the data directory."""

    @pytest.fixture
    def real_instances_dir(self):
        """Get path to real instances directory."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, "data", "instances", "small")

    @pytest.mark.slow
    def test_verify_all_small_instances(self, real_instances_dir):
        """Test verifying all small instance files."""
        from backup.core.generator.instance_verificator import InstanceVerificator
        import io
        import sys
        
        if not os.path.exists(real_instances_dir):
            pytest.skip("Real instances directory not found")
        
        instance_files = [f for f in os.listdir(real_instances_dir) if f.endswith('.dat')]
        
        if not instance_files:
            pytest.skip("No instance files found")
        
        # Test up to 5 instances to avoid slow tests
        for filename in instance_files[:5]:
            filepath = os.path.join(real_instances_dir, filename)
            verificator = InstanceVerificator(filepath)
            
            # Suppress stdout
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                is_valid = verificator.verify()
            finally:
                sys.stdout = old_stdout
            
            assert is_valid, f"Instance {filename} failed verification: {verificator.errors}"

    @pytest.mark.slow
    def test_parse_all_small_instances(self, real_instances_dir):
        """Test parsing all small instance files."""
        from backup.core.model.utils import parse_instance
        
        if not os.path.exists(real_instances_dir):
            pytest.skip("Real instances directory not found")
        
        instance_files = [f for f in os.listdir(real_instances_dir) if f.endswith('.dat')]
        
        if not instance_files:
            pytest.skip("No instance files found")
        
        # Test up to 5 instances
        for filename in instance_files[:5]:
            filepath = os.path.join(real_instances_dir, filename)
            instance = parse_instance(filepath)
            
            # Basic sanity checks
            assert instance.num_products >= 1
            assert instance.num_camions >= 1
            assert instance.num_depots >= 1
            assert instance.num_garages >= 1
            assert instance.num_stations >= 1
            assert len(instance.camions) == instance.num_camions
            assert len(instance.depots) == instance.num_depots
            assert len(instance.garages) == instance.num_garages
            assert len(instance.stations) == instance.num_stations


class TestCategoryGeneration:
    """Test category-based generation from batch_generator."""

    def test_category_configs_exist(self):
        """Test that category configurations are defined."""
        from backup.core.generator.batch_generator import CATEGORIES
        
        assert "small" in CATEGORIES
        assert "medium" in CATEGORIES
        assert "large" in CATEGORIES

    def test_category_config_structure(self):
        """Test that category configurations have required fields."""
        from backup.core.generator.batch_generator import CATEGORIES
        
        required_fields = [
            "description", "nb_stations", "nb_vehicules", "nb_produits",
            "nb_depots", "nb_garages", "transition_cost", "capacity",
            "demand", "grid_size"
        ]
        
        for category_name, config in CATEGORIES.items():
            for field in required_fields:
                assert field in config, f"Category {category_name} missing field {field}"

    def test_generate_random_params(self):
        """Test random parameter generation for categories."""
        from backup.core.generator.batch_generator import generate_random_params, CATEGORIES
        import random
        
        random.seed(42)
        
        for category_name in ["small", "medium", "large"]:
            params = generate_random_params(category_name)
            config = CATEGORIES[category_name]
            
            # Check params are within category bounds
            assert config["nb_stations"][0] <= params["nb_s"] <= config["nb_stations"][1]
            assert config["nb_vehicules"][0] <= params["nb_v"] <= config["nb_vehicules"][1]
            assert config["nb_produits"][0] <= params["nb_p"] <= config["nb_produits"][1]
            assert config["nb_depots"][0] <= params["nb_d"] <= config["nb_depots"][1]
            assert config["nb_garages"][0] <= params["nb_g"] <= config["nb_garages"][1]


class TestSolutionParsing:
    """Test parsing solution files."""

    @pytest.fixture
    def real_solutions_dir(self):
        """Get path to real solutions directory."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, "data", "solutions")

    def test_parse_real_solution(self, real_solutions_dir):
        """Test parsing a real solution file."""
        from backup.core.model.utils import parse_solution
        
        if not os.path.exists(real_solutions_dir):
            pytest.skip("Solutions directory not found")
        
        solution_files = [f for f in os.listdir(real_solutions_dir) 
                        if f.endswith('.dat') and f.startswith('Sol_')]
        
        if not solution_files:
            pytest.skip("No solution files found")
        
        filepath = os.path.join(real_solutions_dir, solution_files[0])
        solution = parse_solution(filepath)
        
        # Basic sanity checks
        assert len(solution.vehicles) >= 1
        assert "used_vehicles" in solution.metrics
        assert "total_changes" in solution.metrics
        assert "total_switch_cost" in solution.metrics
        assert "distance_total" in solution.metrics
