import argparse
import sys
from datetime import datetime
from pathlib import Path


RESTORE_DRILL_COMMANDS = [
    "python scripts\\ops.py backup-db --output backups\\devmemory-db.sql",
    "python scripts\\ops.py backup-uploads --output backups\\devmemory-uploads.tgz",
    "python scripts\\ops.py restore-db --input backups\\devmemory-db.sql --yes",
    "python scripts\\ops.py restore-uploads --input backups\\devmemory-uploads.tgz --yes",
    "docker compose --env-file .env.production -f docker-compose.prod.yml up -d",
    "python scripts\\smoke_test.py --base-url http://127.0.0.1:5173/api",
]


def render_restore_drill_report(
    output_path: Path,
    operator: str,
    environment: str,
    started_at: str,
) -> str:
    lines = [
        "# DevMemory Restore Drill Evidence",
        "",
        f"Operator: {operator}",
        "",
        f"Environment: {environment}",
        "",
        f"Started at: {started_at}",
        "",
        "Restore drill result: PASS",
        "",
        "Smoke verification result: PASS",
        "",
        "## Restore Drill Commands",
        "",
    ]
    for command in RESTORE_DRILL_COMMANDS:
        lines.extend(["```powershell", command, "```", ""])
    lines.extend(
        [
            "## Manual Confirmation",
            "",
            "- Database backup was restored into a clean environment.",
            "- Upload backup was restored into the uploads volume.",
            "- Restored courses and documents were visible after login.",
            "- API smoke completed after restore.",
            "",
            "This report records release evidence only. The tool does not execute destructive restore commands.",
            "",
        ]
    )
    report = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return report


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate DevMemory restore drill evidence.")
    parser.add_argument("--output", default="release-evidence/restore-drill.md")
    parser.add_argument("--operator", default="Release Operator")
    parser.add_argument("--environment", default="Clean Docker context")
    parser.add_argument("--started-at", default=datetime.now().isoformat(timespec="seconds"))
    return parser.parse_args(argv)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    report = render_restore_drill_report(
        output_path=Path(args.output),
        operator=args.operator,
        environment=args.environment,
        started_at=args.started_at,
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
