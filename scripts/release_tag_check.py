import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


REQUIRED_RELEASE_NOTE_SECTIONS = [
    "## Release Summary",
    "## Deployment Notes",
    "## Verification Evidence",
    "## Known Risks",
    "## Deferred to v1.1",
]

REQUIRED_RESTORE_EVIDENCE_FIELDS = [
    "Operator:",
    "Environment:",
    "Started at:",
    "Restore drill result:",
    "Smoke verification result:",
]


@dataclass(frozen=True)
class ReleaseReadinessResult:
    version: str
    ready: bool
    passed_checks: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


def check_release_readiness(version: str, root: Path | str = ".", git_status: str | None = None) -> ReleaseReadinessResult:
    root_path = Path(root)
    passed_checks = []
    failures = []

    if re.fullmatch(r"v\d+\.\d+\.\d+", version):
        passed_checks.append("version format is valid")
    else:
        failures.append("version must match vMAJOR.MINOR.PATCH, for example v1.0.0")

    status = _git_status(root_path) if git_status is None else git_status
    if status.strip():
        failures.append("git workspace must be clean before tagging")
    else:
        passed_checks.append("git workspace is clean")

    release_notes_path = root_path / "docs" / "release-notes" / f"{version}.md"
    if release_notes_path.exists():
        passed_checks.append("release notes exist")
        release_notes = release_notes_path.read_text(encoding="utf-8")
        for section in REQUIRED_RELEASE_NOTE_SECTIONS:
            if section in release_notes:
                passed_checks.append(f"release notes include {section}")
            else:
                failures.append(f"release notes missing section: {section}")
    else:
        failures.append(f"release notes missing: docs/release-notes/{version}.md")

    checklist = _read_text(root_path / "docs" / "release-checklist.md")
    if version in checklist:
        passed_checks.append(f"release checklist references {version}")
    else:
        failures.append(f"release checklist must reference {version}")
    release_note_links = [f"docs/release-notes/{version}.md", f"release-notes/{version}.md"]
    if any(link in checklist for link in release_note_links):
        passed_checks.append("release checklist links release notes")
    else:
        failures.append(f"release checklist must link docs/release-notes/{version}.md")

    roadmap = _read_text(root_path / "docs" / "professional-release-roadmap.md")
    i008_section = _markdown_section(roadmap, "### I-008 Release Notes and Tagging Preparation")
    if i008_section and "Status: completed" in i008_section:
        passed_checks.append("roadmap marks I-008 completed")
    else:
        failures.append("roadmap must mark I-008 Release Notes and Tagging Preparation completed")

    i009_section = _markdown_section(roadmap, "### I-009 Clean Restore Drill Evidence")
    if i009_section and "Status: completed" in i009_section:
        passed_checks.append("roadmap marks I-009 completed")
    else:
        failures.append("roadmap must mark I-009 Clean Restore Drill Evidence completed")

    iteration_records = list((root_path / "docs" / "iterations").glob("*i008*release*tag*.md"))
    if iteration_records:
        passed_checks.append("I-008 iteration record exists")
    else:
        failures.append("I-008 iteration record missing")

    restore_iteration_records = list((root_path / "docs" / "iterations").glob("*i009*restore*drill*evidence*.md"))
    if restore_iteration_records:
        passed_checks.append("I-009 iteration record exists")
    else:
        failures.append("I-009 iteration record missing")

    restore_evidence_path = root_path / "release-evidence" / "restore-drill.md"
    if restore_evidence_path.exists():
        passed_checks.append("restore drill evidence exists")
        restore_evidence = restore_evidence_path.read_text(encoding="utf-8")
        for field_name in REQUIRED_RESTORE_EVIDENCE_FIELDS:
            if field_name in restore_evidence:
                passed_checks.append(f"restore drill evidence includes {field_name}")
            else:
                failures.append(f"restore drill evidence missing field: {field_name}")
    else:
        failures.append("restore drill evidence missing: release-evidence/restore-drill.md")

    return ReleaseReadinessResult(
        version=version,
        ready=not failures,
        passed_checks=passed_checks,
        failures=failures,
    )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Check whether DevMemory is ready for a release tag.")
    parser.add_argument("--version", required=True, help="Release tag version, for example v1.0.0.")
    return parser.parse_args(argv)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    result = check_release_readiness(args.version)
    print(f"DevMemory release tag readiness: {args.version}")
    print("")
    for check in result.passed_checks:
        print(f"PASS: {check}")
    for failure in result.failures:
        print(f"FAIL: {failure}")
    return 0 if result.ready else 1


def _git_status(root: Path) -> str:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0:
        return completed.stdout or f"git status failed with exit code {completed.returncode}"
    return completed.stdout


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _markdown_section(markdown: str, heading: str) -> str:
    start = markdown.find(heading)
    if start == -1:
        return ""
    next_heading = markdown.find("\n### ", start + len(heading))
    if next_heading == -1:
        return markdown[start:]
    return markdown[start:next_heading]


if __name__ == "__main__":
    raise SystemExit(main())
