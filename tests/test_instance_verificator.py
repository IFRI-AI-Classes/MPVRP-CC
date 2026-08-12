from pathlib import Path

import numpy as np

from backend.core.generation.config import VerificationReport
from backend.core.generation.instance_file_io import load_instance_file
from backend.core.generation.validation import validate_parsed_instance
from backend.paths import WITH_CHANGEOVER_INSTANCES_DIR, WITHOUT_CHANGEOVER_INSTANCES_DIR


def test_all_benchmark_instances_are_canonical_and_paired():
    with_costs = sorted(WITH_CHANGEOVER_INSTANCES_DIR.glob("MPVRP_*.dat"))
    without_costs = sorted(WITHOUT_CHANGEOVER_INSTANCES_DIR.glob("MPVRP_*.dat"))
    assert len(with_costs) == len(without_costs) == 150
    assert [path.name for path in with_costs] == [path.name for path in without_costs]

    for original, zeroed in zip(with_costs, without_costs):
        first_report, second_report = VerificationReport(), VerificationReport()
        first = load_instance_file(original, first_report)
        second = load_instance_file(zeroed, second_report)
        assert first is not None and second is not None
        assert validate_parsed_instance(first).is_valid
        assert validate_parsed_instance(second).is_valid
        assert np.allclose(second.transition_costs, 0)
        for field in ("uuid", "params", "vehicles", "depots", "garages", "stations"):
            assert np.array_equal(getattr(first, field), getattr(second, field))


def test_loader_rejects_missing_uuid(tmp_path):
    path = tmp_path / "invalid.dat"
    path.write_text("1 1 1 1 1\n", encoding="utf-8")
    report = VerificationReport()
    assert load_instance_file(path, report) is None
    assert report.errors
