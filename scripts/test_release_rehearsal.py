from pathlib import Path

from release_rehearsal import RehearsalResult, build_rehearsal_plan, render_report


def test_rehearsal_plan_covers_release_candidate_gates():
    plan = build_rehearsal_plan(base_url="http://127.0.0.1:5173/api")
    names = [step.name for step in plan]

    assert names == [
        "Git workspace status",
        "Backend tests",
        "Frontend tests",
        "Frontend production build",
        "Production compose config",
        "Docker stack rebuild",
        "Docker service status",
        "API smoke test",
    ]
    assert Path(plan[1].command[0]).is_absolute()
    assert plan[1].command[0].endswith(str(Path(".venv") / "Scripts" / "python.exe"))
    assert plan[1].env["TMP"].endswith(str(Path("release-evidence") / "tmp"))
    assert plan[1].env["TEMP"].endswith(str(Path("release-evidence") / "tmp"))
    assert plan[0].fail_on_output is True
    assert plan[4].env["DEVMEMORY_ENV_FILE"] == ".env.production.example"
    assert plan[-1].command == ["python", "scripts/smoke_test.py", "--base-url", "http://127.0.0.1:5173/api"]
    assert plan[-1].attempts == 10
    assert plan[-1].retry_delay_seconds == 3


def test_rehearsal_plan_can_skip_docker_for_ci_like_contexts():
    plan = build_rehearsal_plan(base_url="http://127.0.0.1:5173/api", include_docker=False, allow_dirty=True)
    names = [step.name for step in plan]

    assert "Docker stack rebuild" not in names
    assert "API smoke test" not in names
    assert "Production compose config" in names
    assert plan[0].fail_on_output is False


def test_render_report_records_pass_fail_and_follow_up(tmp_path):
    report = render_report(
        results=[
            RehearsalResult(name="Backend tests", command="pytest tests", exit_code=0, output="63 passed"),
            RehearsalResult(name="API smoke test", command="python scripts/smoke_test.py", exit_code=1, output="timeout"),
        ],
        output_path=tmp_path / "release-candidate.md",
    )

    assert "# DevMemory Release Candidate Rehearsal" in report
    assert "| Backend tests | PASS | `pytest tests` |" in report
    assert "| API smoke test | FAIL | `python scripts/smoke_test.py` |" in report
    assert "timeout" in report
    assert "Backup and restore rehearsal" in report
    assert Path(tmp_path / "release-candidate.md").read_text(encoding="utf-8") == report
