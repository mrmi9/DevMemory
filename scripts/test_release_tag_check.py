from pathlib import Path

from release_tag_check import check_release_readiness


def write_minimal_release_files(root: Path, version: str = "v1.0.0") -> None:
    (root / "docs" / "iterations").mkdir(parents=True)
    (root / "docs" / "release-notes").mkdir(parents=True)
    (root / "docs" / "release-checklist.md").write_text(
        "Release notes: docs/release-notes/v1.0.0.md\nTag: v1.0.0\n",
        encoding="utf-8",
    )
    (root / "docs" / "professional-release-roadmap.md").write_text(
        "### I-008 Release Notes and Tagging Preparation\n\nStatus: completed.\n",
        encoding="utf-8",
    )
    (root / "docs" / "iterations" / "2026-05-29-i008-release-notes-tagging.md").write_text(
        "## Acceptance Gates\n- [x] Release tag readiness check passes.\n",
        encoding="utf-8",
    )
    (root / "docs" / "release-notes" / f"{version}.md").write_text(
        f"# DevMemory {version} Release Notes\n\n"
        "## Release Summary\nPrivate deployment release candidate.\n\n"
        "## Deployment Notes\nUse docker compose.\n\n"
        "## Verification Evidence\nAll release gates pass.\n\n"
        "## Known Risks\nRestore drill must be recorded.\n\n"
        "## Deferred to v1.1\nTeam roles.\n",
        encoding="utf-8",
    )


def test_release_tag_check_accepts_complete_release_notes(tmp_path):
    write_minimal_release_files(tmp_path)

    result = check_release_readiness("v1.0.0", root=tmp_path, git_status="")

    assert result.ready is True
    assert result.failures == []
    assert "release notes exist" in result.passed_checks
    assert "release checklist references v1.0.0" in result.passed_checks


def test_release_tag_check_rejects_missing_required_sections(tmp_path):
    write_minimal_release_files(tmp_path)
    (tmp_path / "docs" / "release-notes" / "v1.0.0.md").write_text(
        "# DevMemory v1.0.0 Release Notes\n\n## Release Summary\nToo thin.\n",
        encoding="utf-8",
    )

    result = check_release_readiness("v1.0.0", root=tmp_path, git_status="")

    assert result.ready is False
    assert "release notes missing section: ## Deployment Notes" in result.failures
    assert "release notes missing section: ## Deferred to v1.1" in result.failures


def test_release_tag_check_rejects_dirty_workspace(tmp_path):
    write_minimal_release_files(tmp_path)

    result = check_release_readiness("v1.0.0", root=tmp_path, git_status=" M README.md\n")

    assert result.ready is False
    assert "git workspace must be clean before tagging" in result.failures


def test_release_tag_check_rejects_invalid_version(tmp_path):
    write_minimal_release_files(tmp_path, version="1.0")

    result = check_release_readiness("1.0", root=tmp_path, git_status="")

    assert result.ready is False
    assert "version must match vMAJOR.MINOR.PATCH, for example v1.0.0" in result.failures


def test_release_tag_check_requires_i008_section_to_be_completed(tmp_path):
    write_minimal_release_files(tmp_path)
    (tmp_path / "docs" / "professional-release-roadmap.md").write_text(
        "### I-007 Release Candidate Rehearsal\n\nStatus: completed.\n\n"
        "### I-008 Release Notes and Tagging Preparation\n\nDefault scope:\n- Add release notes.\n",
        encoding="utf-8",
    )

    result = check_release_readiness("v1.0.0", root=tmp_path, git_status="")

    assert result.ready is False
    assert "roadmap must mark I-008 Release Notes and Tagging Preparation completed" in result.failures


def test_release_tag_check_accepts_checklist_relative_release_note_link(tmp_path):
    write_minimal_release_files(tmp_path)
    (tmp_path / "docs" / "release-checklist.md").write_text(
        "Review [release-notes/v1.0.0.md](release-notes/v1.0.0.md).\n",
        encoding="utf-8",
    )

    result = check_release_readiness("v1.0.0", root=tmp_path, git_status="")

    assert result.ready is True
    assert "release checklist links release notes" in result.passed_checks
