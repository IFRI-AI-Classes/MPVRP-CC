import zipfile

from backend.core.scoring import score_evaluation


def test_missing_and_invalid_archives_fail_cleanly(tmp_path):
    missing = tmp_path / "missing.zip"
    assert not score_evaluation.process_full_submission(str(missing))["ok"]
    invalid = tmp_path / "invalid.zip"
    invalid.write_text("not a zip")
    assert not score_evaluation.process_full_submission(str(invalid))["ok"]
    assert not invalid.exists()


def test_submission_is_evaluated_against_official_cost_instances(tmp_path, monkeypatch):
    instances = tmp_path / "instances"
    instances.mkdir()
    (instances / "MPVRP_001_s1_d1_p1.dat").write_text("instance")
    archive = tmp_path / "submission.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("nested/Sol_001.dat", "solution")

    monkeypatch.setattr(score_evaluation, "WITH_CHANGEOVER_INSTANCES_DIR", instances)
    monkeypatch.setattr(score_evaluation, "EXPECTED_INSTANCE_COUNT", 1)
    monkeypatch.setattr(score_evaluation, "parse_instance", lambda _: object())
    monkeypatch.setattr(score_evaluation, "parse_solution", lambda _: object())
    monkeypatch.setattr(
        score_evaluation,
        "verify_solution",
        lambda *_: ([], {"distance_total": 12.5, "total_switch_cost": 3.5}),
    )
    result = score_evaluation.process_full_submission(str(archive))
    assert result["ok"]
    assert result["is_fully_feasible"]
    assert result["total_weighted_score"] == 16
    assert result["instance_results"][0]["category"] == "with_changeover_costs"


def test_partial_submission_penalizes_invalid_and_missing_solutions_equally(tmp_path, monkeypatch):
    instances = tmp_path / "instances"
    instances.mkdir()
    for instance_id in ("001", "002", "003"):
        (instances / f"MPVRP_{instance_id}_s1_d1_p1.dat").write_text("instance")

    archive = tmp_path / "partial.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("solutions/Sol_001.dat", "valid solution")
        bundle.writestr("solutions/Sol_002.dat", "unresolved solution")

    monkeypatch.setattr(score_evaluation, "WITH_CHANGEOVER_INSTANCES_DIR", instances)
    monkeypatch.setattr(score_evaluation, "EXPECTED_INSTANCE_COUNT", 3)
    monkeypatch.setattr(score_evaluation, "parse_instance", lambda _: object())

    def parse_submitted_solution(path):
        if path.endswith("Sol_002.dat"):
            raise ValueError("solution cannot be read")
        return object()

    monkeypatch.setattr(score_evaluation, "parse_solution", parse_submitted_solution)
    monkeypatch.setattr(
        score_evaluation,
        "verify_solution",
        lambda *_: ([], {"distance_total": 12.5, "total_switch_cost": 3.5}),
    )

    result = score_evaluation.process_full_submission(str(archive))

    assert result["ok"]
    assert result["total_feasible_count"] == 1
    assert result["total_weighted_score"] == 16 + 2 * score_evaluation.BIG_M
    assert "Parsing or verification error" in result["instance_results"][1]["errors"][0]
    assert "Missing solution" in result["instance_results"][2]["errors"][0]
    assert "Recognized solutions: 2/3" in result["processor_info"]
