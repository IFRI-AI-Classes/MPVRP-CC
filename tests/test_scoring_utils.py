import zipfile

from backend.core.scoring.score_evaluation import _index_solutions, _safe_extract


def test_solution_index_accepts_canonical_and_short_names(tmp_path):
    (tmp_path / "Sol_001.dat").write_text("one")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "Sol_MPVRP_002_s4_d1_p2.dat").write_text("two")
    selected, warnings = _index_solutions(tmp_path)
    assert set(selected) == {"001", "002"}
    assert not warnings


def test_safe_extract_rejects_path_traversal(tmp_path):
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../escape.dat", "bad")
    destination = tmp_path / "out"
    destination.mkdir()
    assert "Unsafe" in _safe_extract(archive, destination)


def test_solution_index_rejects_duplicate_ids(tmp_path):
    (tmp_path / "Sol_001.dat").write_text("short")
    (tmp_path / "Sol_MPVRP_001_demo.dat").write_text("long")
    selected, warnings = _index_solutions(tmp_path)
    assert "001" not in selected
    assert any("duplicate" in warning for warning in warnings)
