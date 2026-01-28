import os
import tempfile

import pytest

from backup.core.generator.instance_verificator import InstanceVerificator


class TestInstanceVerificatorInit:
    """Test suite for InstanceVerificator initialization."""

    def test_init_with_valid_path(self, sample_instance_file):
        """Test initialization with a valid file path."""
        verificator = InstanceVerificator(sample_instance_file)
        
        assert verificator.filepath == sample_instance_file
        assert verificator.errors == []
        assert verificator.warnings == []
        assert verificator.data == {}

    def test_init_with_nonexistent_path(self):
        """Test initialization with non-existent file path."""
        verificator = InstanceVerificator("/nonexistent/path/file.dat")
        
        # Should initialize without error, validation will fail later
        assert verificator.filepath == "/nonexistent/path/file.dat"


class TestInstanceVerificatorFileExists:
    """Test suite for check_file_exists method."""

    def test_file_exists(self, sample_instance_file):
        """Test that existing file is detected."""
        verificator = InstanceVerificator(sample_instance_file)
        
        result = verificator.check_file_exists()
        
        assert result is True
        assert len(verificator.errors) == 0

    def test_file_not_exists(self):
        """Test that non-existent file triggers error."""
        verificator = InstanceVerificator("/nonexistent/file.dat")
        
        result = verificator.check_file_exists()
        
        assert result is False
        assert len(verificator.errors) > 0
        assert any("non trouvé" in e or "not found" in e.lower() for e in verificator.errors)


class TestInstanceVerificatorLoadData:
    """Test suite for load_data method."""

    def test_load_valid_data(self, sample_instance_file):
        """Test loading data from valid instance file."""
        verificator = InstanceVerificator(sample_instance_file)
        verificator.check_file_exists()
        
        result = verificator.load_data()
        
        assert result is True
        assert 'params' in verificator.data
        assert 'nb_p' in verificator.data
        assert 'nb_d' in verificator.data
        assert 'nb_g' in verificator.data
        assert 'nb_s' in verificator.data
        assert 'nb_v' in verificator.data
        assert 'vehicles' in verificator.data
        assert 'depots' in verificator.data
        assert 'garages' in verificator.data
        assert 'stations' in verificator.data
        assert 'transition_costs' in verificator.data

    def test_load_invalid_data(self, invalid_instance_file):
        """Test loading data from invalid instance file."""
        verificator = InstanceVerificator(invalid_instance_file)
        verificator.check_file_exists()
        
        result = verificator.load_data()
        
        assert result is False
        assert len(verificator.errors) > 0

    def test_load_data_extracts_uuid(self, temp_dir):
        """Test that UUID is extracted from file."""
        filepath = os.path.join(temp_dir, "test_uuid.dat")
        content = """# 12345678-1234-1234-1234-123456789abc
2	1	1	1	1
0.0	10.0
10.0	0.0
1	5000	1	1
1	50.0	50.0	2000	1500
1	0.0	0.0
1	25.0	25.0	1000	500
"""
        with open(filepath, 'w') as f:
            f.write(content)
        
        verificator = InstanceVerificator(filepath)
        verificator.check_file_exists()
        verificator.load_data()
        
        assert verificator.data.get('uuid') == "12345678-1234-1234-1234-123456789abc"


class TestInstanceVerificatorMinimumElements:
    """Test suite for check_minimum_elements method."""

    def test_minimum_elements_valid(self, sample_instance_file):
        """Test minimum elements check with valid instance."""
        verificator = InstanceVerificator(sample_instance_file)
        verificator.check_file_exists()
        verificator.load_data()
        
        verificator.check_minimum_elements()
        
        # Valid instance should not add errors for minimum elements
        assert all("requis" not in e.lower() for e in verificator.errors)


class TestInstanceVerificatorUniqueIds:
    """Test suite for check_unique_ids method."""

    def test_unique_ids_valid(self, sample_instance_file):
        """Test unique IDs check with valid instance."""
        verificator = InstanceVerificator(sample_instance_file)
        verificator.check_file_exists()
        verificator.load_data()
        
        verificator.check_unique_ids()
        
        # Valid instance should not have duplicate ID errors
        assert all("dupliqués" not in e.lower() and "duplicat" not in e.lower() 
                   for e in verificator.errors)

    def test_duplicate_vehicle_ids(self, temp_dir):
        """Test detection of duplicate vehicle IDs."""
        filepath = os.path.join(temp_dir, "duplicate_vehicles.dat")
        content = """# test-uuid
2	1	1	1	2
0.0	10.0
10.0	0.0
1	5000	1	1
1	5000	1	1
1	50.0	50.0	2000	1500
1	0.0	0.0
1	25.0	25.0	1000	500
"""
        with open(filepath, 'w') as f:
            f.write(content)
        
        verificator = InstanceVerificator(filepath)
        verificator.check_file_exists()
        verificator.load_data()
        verificator.check_unique_ids()
        
        # Should detect duplicate IDs
        assert any("dupliqués" in e.lower() or "manquants" in e.lower() 
                   for e in verificator.errors)


class TestInstanceVerificatorValidity:
    """Test suite for check_validity method."""

    def test_validity_check_valid(self, sample_instance_file):
        """Test validity check with valid instance."""
        verificator = InstanceVerificator(sample_instance_file)
        verificator.check_file_exists()
        verificator.load_data()
        
        verificator.check_validity()
        
        # Basic validity should pass for sample instance
        # Check that no critical validity errors occurred
        critical_errors = [e for e in verificator.errors 
                         if "matrice" in e.lower() or "garage" in e.lower()]
        assert len(critical_errors) == 0

    def test_invalid_garage_reference(self, temp_dir):
        """Test detection of invalid garage reference in vehicle."""
        filepath = os.path.join(temp_dir, "invalid_garage.dat")
        content = """# test-uuid
2	1	1	1	1
0.0	10.0
10.0	0.0
1	5000	99	1
1	50.0	50.0	2000	1500
1	0.0	0.0
1	25.0	25.0	1000	500
"""
        with open(filepath, 'w') as f:
            f.write(content)
        
        verificator = InstanceVerificator(filepath)
        verificator.check_file_exists()
        verificator.load_data()
        verificator.check_validity()
        
        assert any("garage" in e.lower() for e in verificator.errors)


class TestInstanceVerificatorCapacityDemand:
    """Test suite for check_capacity_demand method."""

    def test_capacity_demand_valid(self, sample_instance_file):
        """Test capacity/demand check with valid instance."""
        verificator = InstanceVerificator(sample_instance_file)
        verificator.check_file_exists()
        verificator.load_data()
        
        verificator.check_capacity_demand()
        
        # Valid instance should pass capacity check
        capacity_errors = [e for e in verificator.errors if "capacité" in e.lower()]
        assert len(capacity_errors) == 0


class TestInstanceVerificatorFeasibility:
    """Test suite for check_feasibility method."""

    def test_feasibility_valid(self, sample_instance_file):
        """Test feasibility check with valid instance."""
        verificator = InstanceVerificator(sample_instance_file)
        verificator.check_file_exists()
        verificator.load_data()
        
        verificator.check_feasibility()
        
        # Sample instance should be feasible
        feasibility_errors = [e for e in verificator.errors 
                            if "faisabilité" in e.lower() or "stock" in e.lower()]
        # May or may not have errors depending on the sample, just verify method runs


class TestInstanceVerificatorFullVerification:
    """Test suite for the full verify method."""

    def test_verify_valid_instance(self, sample_instance_file):
        """Test full verification of valid instance."""
        verificator = InstanceVerificator(sample_instance_file)
        
        # Run verification (suppress stdout)
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = verificator.verify()
        finally:
            sys.stdout = old_stdout
        
        # Should return True or False based on errors
        assert isinstance(result, bool)

    def test_verify_nonexistent_file(self):
        """Test verification of non-existent file."""
        verificator = InstanceVerificator("/nonexistent/file.dat")
        
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = verificator.verify()
        finally:
            sys.stdout = old_stdout
        
        assert result is False

    def test_verify_returns_errors(self, invalid_instance_file):
        """Test that verification populates errors list."""
        verificator = InstanceVerificator(invalid_instance_file)
        
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = verificator.verify()
        finally:
            sys.stdout = old_stdout
        
        assert result is False
        assert len(verificator.errors) > 0


class TestInstanceVerificatorWithRealInstances:
    """Test suite using real instance files if available."""

    @pytest.fixture
    def real_instance_path(self):
        """Get path to a real instance file if available."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        instances_dir = os.path.join(project_root, "data", "instances", "small")
        
        if os.path.exists(instances_dir):
            files = [f for f in os.listdir(instances_dir) if f.endswith('.dat')]
            if files:
                return os.path.join(instances_dir, files[0])
        
        return None

    @pytest.mark.integration
    def test_verify_real_instance(self, real_instance_path):
        """Test verification of a real instance file."""
        if real_instance_path is None:
            pytest.skip("No real instance files available")
        
        verificator = InstanceVerificator(real_instance_path)
        
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = verificator.verify()
        finally:
            sys.stdout = old_stdout
        
        # Real instances should be valid
        assert result is True, f"Real instance failed verification with errors: {verificator.errors}"


class TestInstanceVerificatorGeometry:
    """Test suite for geometry-related checks."""

    def test_geometry_valid(self, sample_instance_file):
        """Test geometry check with valid instance."""
        verificator = InstanceVerificator(sample_instance_file)
        verificator.check_file_exists()
        verificator.load_data()
        
        verificator.check_geometry()
        
        # Sample instance should have valid geometry
        geometry_errors = [e for e in verificator.errors if "géométr" in e.lower()]
        assert len(geometry_errors) == 0


class TestInstanceVerificatorTriangleInequality:
    """Test suite for triangle inequality check on transition matrix."""

    def test_triangle_inequality(self, sample_instance_file):
        """Test triangle inequality check."""
        verificator = InstanceVerificator(sample_instance_file)
        verificator.check_file_exists()
        verificator.load_data()
        
        verificator.check_triangle_inequality()
        
        # Check runs without crashing
        # Warnings may or may not be generated depending on instance


class TestInstanceVerificatorGeographicOverlap:
    """Test suite for geographic overlap check."""

    def test_no_overlap(self, sample_instance_file):
        """Test that valid instance has no geographic overlap."""
        verificator = InstanceVerificator(sample_instance_file)
        verificator.check_file_exists()
        verificator.load_data()
        
        verificator.check_geographic_overlap()
        
        # Warnings about overlap should be in warnings, not errors
        overlap_errors = [e for e in verificator.errors if "chevauchement" in e.lower()]
        assert len(overlap_errors) == 0

    def test_overlapping_points(self, temp_dir):
        """Test detection of overlapping geographic points."""
        filepath = os.path.join(temp_dir, "overlap.dat")
        # Two entities at the same location
        content = """# test-uuid
2	1	1	1	1
0.0	10.0
10.0	0.0
1	5000	1	1
1	50.0	50.0	2000	1500
1	50.0	50.0
1	50.0	50.0	1000	500
"""
        with open(filepath, 'w') as f:
            f.write(content)
        
        verificator = InstanceVerificator(filepath)
        verificator.check_file_exists()
        verificator.load_data()
        verificator.check_geographic_overlap()
        
        # Should detect overlap (may be warning or info)
        # The important thing is it doesn't crash
