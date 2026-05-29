import argparse
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class RehearsalStep:
    name: str
    command: list[str]
    cwd: str = "."
    env: dict[str, str] = field(default_factory=dict)
    fail_on_output: bool = False
    attempts: int = 1
    retry_delay_seconds: int = 0


@dataclass(frozen=True)
class RehearsalResult:
    name: str
    command: str
    exit_code: int
    output: str


def build_rehearsal_plan(
    base_url: str,
    env_file: str = ".env.production.example",
    compose_file: str = "docker-compose.prod.yml",
    include_docker: bool = True,
    allow_dirty: bool = False,
) -> list[RehearsalStep]:
    plan = [
        RehearsalStep("Git workspace status", ["git", "status", "--porcelain"], fail_on_output=not allow_dirty),
        RehearsalStep("Backend tests", [_python_executable(), "-m", "pytest", "tests"], cwd="backend", env=_temp_env()),
        RehearsalStep("Frontend tests", ["npm.cmd", "test"], cwd="frontend"),
        RehearsalStep("Frontend production build", ["npm.cmd", "run", "build"], cwd="frontend"),
        RehearsalStep(
            "Production compose config",
            ["docker", "compose", "--env-file", env_file, "-f", compose_file, "config"],
            env={"DEVMEMORY_ENV_FILE": env_file},
        ),
    ]
    if include_docker:
        plan.extend(
            [
                RehearsalStep("Docker stack rebuild", ["docker", "compose", "up", "--build", "-d"]),
                RehearsalStep("Docker service status", ["docker", "compose", "ps"]),
                RehearsalStep(
                    "API smoke test",
                    ["python", "scripts/smoke_test.py", "--base-url", base_url],
                    attempts=10,
                    retry_delay_seconds=3,
                ),
            ]
        )
    return plan


def run_rehearsal(plan: list[RehearsalStep]) -> list[RehearsalResult]:
    results = []
    for step in plan:
        completed = _run_step(step)
        exit_code = completed.returncode
        if step.fail_on_output and completed.returncode == 0 and completed.stdout.strip():
            exit_code = 1
        results.append(
            RehearsalResult(
                name=step.name,
                command=_format_command(step.command),
                exit_code=exit_code,
                output=completed.stdout.strip(),
            )
        )
        if exit_code != 0:
            break
    return results


def _run_step(step: RehearsalStep):
    last_completed = None
    outputs = []
    for attempt in range(1, step.attempts + 1):
        completed = subprocess.run(
            step.command,
            cwd=step.cwd,
            env={**_base_env(), **step.env},
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        outputs.append(f"[attempt {attempt}/{step.attempts}]\n{completed.stdout.strip()}")
        last_completed = completed
        if completed.returncode == 0:
            break
        if attempt < step.attempts and step.retry_delay_seconds:
            time.sleep(step.retry_delay_seconds)
    last_completed.stdout = "\n\n".join(outputs)
    return last_completed


def render_report(results: list[RehearsalResult], output_path: Path) -> str:
    generated_at = datetime.now().isoformat(timespec="seconds")
    lines = [
        "# DevMemory Release Candidate Rehearsal",
        "",
        f"Generated at: `{generated_at}`",
        "",
        "## Gate Results",
        "",
        "| Gate | Result | Command |",
        "| --- | --- | --- |",
    ]
    for result in results:
        status = "PASS" if result.exit_code == 0 else "FAIL"
        lines.append(f"| {result.name} | {status} | `{result.command}` |")
    lines.extend(["", "## Evidence", ""])
    for result in results:
        lines.extend(
            [
                f"### {result.name}",
                "",
                f"- Exit code: `{result.exit_code}`",
                f"- Command: `{result.command}`",
                "",
                "```text",
                _trim_output(result.output),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Backup and restore rehearsal",
            "",
            "A release candidate is not ready until database and upload backups have been restored in a clean environment.",
            "",
            "Recommended commands:",
            "",
            "```powershell",
            "python scripts\\ops.py backup-db --output backups\\devmemory-db.sql",
            "python scripts\\ops.py backup-uploads --output backups\\devmemory-uploads.tgz",
            "python scripts\\ops.py restore-db --input backups\\devmemory-db.sql --yes",
            "python scripts\\ops.py restore-uploads --input backups\\devmemory-uploads.tgz --yes",
            "python scripts\\smoke_test.py --base-url http://127.0.0.1:5173/api",
            "```",
            "",
            "Record the clean-environment restore result in this report before tagging a release.",
            "",
        ]
    )
    report = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return report


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run DevMemory release candidate rehearsal gates.")
    parser.add_argument("--base-url", default="http://127.0.0.1:5173/api")
    parser.add_argument("--env-file", default=".env.production.example")
    parser.add_argument("--compose-file", default="docker-compose.prod.yml")
    parser.add_argument("--output", default="release-evidence/release-candidate-rehearsal.md")
    parser.add_argument("--skip-docker", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    plan = build_rehearsal_plan(
        base_url=args.base_url,
        env_file=args.env_file,
        compose_file=args.compose_file,
        include_docker=not args.skip_docker,
        allow_dirty=args.allow_dirty,
    )
    results = run_rehearsal(plan)
    report = render_report(results, Path(args.output))
    print(report)
    return 0 if all(result.exit_code == 0 for result in results) else 1


def _base_env():
    import os

    return dict(os.environ)


def _python_executable() -> str:
    return str((Path(".venv") / "Scripts" / "python.exe").resolve())


def _temp_env() -> dict[str, str]:
    temp_dir = str((Path("release-evidence") / "tmp").resolve())
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    return {"TMP": temp_dir, "TEMP": temp_dir, "TMPDIR": temp_dir}


def _format_command(command: list[str]) -> str:
    return " ".join(command)


def _trim_output(output: str, limit: int = 4000) -> str:
    if len(output) <= limit:
        return output
    return output[-limit:]


if __name__ == "__main__":
    raise SystemExit(main())
