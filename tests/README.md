# MPVRP-CC Test Suite

This directory contains the test suite for the MPVRP-CC (Multi-Product Vehicle Routing Problem with Changeover Cost) project.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared fixtures and pytest configuration
├── pytest.ini               # Pytest settings (in project root)
├── fixtures/                # Test data files
│   ├── __init__.py
│   ├── sample_instance.dat  # Sample valid instance
│   ├── sample_solution.dat  # Sample valid solution
│   └── invalid_instance.dat # Invalid instance for error testing
├── test_schemas.py          # Tests for data classes/schemas
├── test_utils.py            # Tests for utility functions
├── test_instance_generator.py   # Tests for instance generation
├── test_instance_verificator.py # Tests for instance verification
├── test_feasibility.py      # Tests for solution feasibility checking
├── test_api.py              # Tests for FastAPI endpoints
└── test_integration.py      # End-to-end integration tests
```

## Running Tests

### Prerequisites

Install test dependencies:

```bash
# Using pip
pip install pytest pytest-cov httpx

# Or using uv with optional dependencies
uv pip install -e ".[test]"
```

### Run All Tests

```bash
pytest
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Specific Test File

```bash
pytest tests/test_schemas.py
```

### Run Specific Test Class or Function

```bash
# Run a specific class
pytest tests/test_schemas.py::TestCamion

# Run a specific test
pytest tests/test_schemas.py::TestCamion::test_camion_creation
```

### Run Tests by Marker

```bash
# Run only integration tests
pytest -m integration

# Run only API tests
pytest -m api

# Skip slow tests
pytest -m "not slow"
```

### Run with Coverage

```bash
pytest --cov=backup --cov-report=html
```

This generates an HTML coverage report in `htmlcov/`.

## Test Categories

### Unit Tests

- `test_schemas.py` - Data class validation
- `test_utils.py` - Utility function testing
- `test_instance_generator.py` - Instance generation logic
- `test_instance_verificator.py` - Instance verification logic
- `test_feasibility.py` - Solution feasibility checking

### Integration Tests

- `test_api.py` - FastAPI endpoint testing
- `test_integration.py` - End-to-end workflows

## Test Markers

- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API-related tests

## Fixtures

Common fixtures are defined in `conftest.py`:

- `sample_camion` - Sample vehicle object
- `sample_depot` - Sample depot object
- `sample_garage` - Sample garage object
- `sample_station` - Sample station object
- `sample_instance` - Complete sample instance
- `sample_solution` - Sample parsed solution
- `temp_dir` - Temporary directory for test files
- `sample_instance_file` - Path to temporary instance file
- `sample_solution_file` - Path to temporary solution file
- `instance_generation_params` - Standard generation parameters

## Writing New Tests

1. Create test functions starting with `test_`
2. Use fixtures from `conftest.py` for common setup
3. Group related tests in classes starting with `Test`
4. Add appropriate markers for categorization
5. Use descriptive docstrings for test documentation

Example:

```python
import pytest

class TestNewFeature:
    """Test suite for new feature."""
    
    def test_basic_functionality(self, sample_instance):
        """Test basic functionality works."""
        result = new_feature(sample_instance)
        assert result is not None
    
    @pytest.mark.slow
    def test_heavy_computation(self):
        """Test computationally intensive operation."""
        # ...
```

## Continuous Integration

Tests are designed to work in CI/CD pipelines:

```bash
# Run all tests with coverage for CI
pytest --cov=backup --cov-report=xml -v

# Run quick tests only
pytest -m "not slow" -v
```
