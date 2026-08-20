from dataclasses import replace

import numpy as np

from backend.core.generation.config import GenerationConfig
from backend.core.generation.instance_file_io import load_instance_file
from backend.core.generation.instance_generator import generate, generate_instance_data
from backend.core.generation.validation import validate_generation_config, validate_instance_data


def test_generation_config_rejects_invalid_dimensions(tmp_path):
    config = GenerationConfig("bad", 0, 1, 1, 1, 1, output_dir=tmp_path)
    assert not validate_generation_config(config).is_valid


def test_generator_is_reproducible_except_uuid(tmp_path):
    config = GenerationConfig("one", 3, 2, 1, 6, 3, output_dir=tmp_path, seed=42)
    first = generate_instance_data(config)
    second = generate_instance_data(config)
    for field in ("params", "transition_costs", "vehicles", "depots", "garages", "stations"):
        assert np.array_equal(getattr(first, field), getattr(second, field))


def test_generate_writes_a_valid_canonical_file(tmp_path):
    config = GenerationConfig("demo", 4, 2, 2, 8, 3, output_dir=tmp_path, seed=7)
    path = generate(config)
    report = __import__("backend.core.generation.config", fromlist=["VerificationReport"]).VerificationReport()
    parsed = load_instance_file(path, report)
    assert parsed is not None
    assert report.is_valid
    assert validate_instance_data(parsed).is_valid


def test_changeover_levels_are_supported(tmp_path):
    base = GenerationConfig("demo", 3, 2, 1, 5, 3, output_dir=tmp_path, seed=11)
    for level in ("low", "normal", "high", "mixed"):
        data = generate_instance_data(replace(base, changeover_cost_level=level))
        assert np.all((np.diag(data.transition_costs) >= 25) & (np.diag(data.transition_costs) <= 150))
        assert np.all(data.transition_costs >= 0)
