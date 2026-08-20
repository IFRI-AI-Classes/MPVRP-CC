from pathlib import Path

import numpy as np

from backend.core.experiments.create_changeover_scenarios import zero_changeover_costs
from backend.core.experiments.reevaluate_changeover_costs import reevaluate_solution_text
from backend.core.generation.config import GenerationConfig
from backend.core.generation.instance_generator import generate
from backend.core.model.utils import parse_instance
from backend.paths import WITH_CHANGEOVER_INSTANCES_DIR


def test_generate_then_parse_workflow(tmp_path):
    path = generate(GenerationConfig("workflow", 4, 2, 2, 8, 3, output_dir=tmp_path, seed=23))
    instance = parse_instance(str(path))
    assert instance.num_products == 3
    assert instance.num_camions == 4
    assert instance.num_stations == 8


def test_create_zero_cost_twin_preserves_everything_else(tmp_path):
    source = next(WITH_CHANGEOVER_INSTANCES_DIR.glob("MPVRP_*.dat"))
    destination = tmp_path / source.name
    zero_changeover_costs(source, destination)
    original_lines = source.read_text().splitlines()
    paired_lines = destination.read_text().splitlines()
    products = int(original_lines[1].split()[0])
    assert original_lines[:2] == paired_lines[:2]
    assert original_lines[2 + products :] == paired_lines[2 + products :]
    assert all(set(line.split()) <= {"0"} for line in paired_lines[2 : 2 + products])


def test_reevaluation_charges_each_loading_including_same_product(sample_instance):
    sample_instance.costs[(0, 0)] = 42.0
    solution = """1: 1 - 1 [1000] - 1 (1000) - 1 [500] - 2 (500) - 1
1: 0(0.00) - 0(0.00) - 0(0.00) - 0(0.00) - 0(0.00)

1
0
0.00
0.00
test
0.100
"""

    updated, changes, cost = reevaluate_solution_text(solution, sample_instance)

    assert changes == 0
    assert cost == 84.0
    assert "0(42.00) - 0(42.00) - 0(84.00) - 0(84.00)" in updated


def test_official_instances_are_parseable():
    paths = sorted(WITH_CHANGEOVER_INSTANCES_DIR.glob("MPVRP_*.dat"))
    assert len(paths) == 100
    for path in paths:
        assert parse_instance(str(path)).num_stations > 0
