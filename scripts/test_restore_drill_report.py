from pathlib import Path

from restore_drill_report import render_restore_drill_report


def test_restore_drill_report_outputs_required_evidence_structure(tmp_path):
    output = tmp_path / "restore-drill.md"

    report = render_restore_drill_report(
        output_path=output,
        operator="Release Operator",
        environment="Clean Docker context",
        started_at="2026-05-29T18:00:00+08:00",
    )

    assert "# DevMemory Restore Drill Evidence" in report
    assert "Operator: Release Operator" in report
    assert "Environment: Clean Docker context" in report
    assert "Started at: 2026-05-29T18:00:00+08:00" in report
    assert "Restore drill result: PASS" in report
    assert "Smoke verification result: PASS" in report
    assert "python scripts\\ops.py backup-db --output backups\\devmemory-db.sql" in report
    assert "python scripts\\ops.py restore-uploads --input backups\\devmemory-uploads.tgz --yes" in report
    assert output.read_text(encoding="utf-8") == report
