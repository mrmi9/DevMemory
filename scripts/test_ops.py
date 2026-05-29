import pytest
from pathlib import Path

from ops import OpsConfig, build_command, parse_args


def test_backup_database_uses_production_compose_and_output_file():
    args = parse_args(["backup-db", "--output", "backups/devmemory-db.sql"])
    command = build_command(args, OpsConfig())

    assert command == [
        "docker",
        "compose",
        "--env-file",
        ".env.production",
        "-f",
        "docker-compose.prod.yml",
        "exec",
        "-T",
        "postgres",
        "pg_dump",
        "-U",
        "study",
        "-d",
        "study",
    ]
    assert args.output == "backups/devmemory-db.sql"


def test_backup_uploads_mounts_named_volume_and_backup_directory():
    args = parse_args(["backup-uploads", "--output", "backups/devmemory-uploads.tgz"])
    command = build_command(args, OpsConfig())
    backup_dir = str(Path("backups").resolve())

    assert command == [
        "docker",
        "run",
        "--rm",
        "-v",
        "devmemory_uploads:/data:ro",
        "-v",
        f"{backup_dir}:/backup",
        "busybox",
        "tar",
        "czf",
        "/backup/devmemory-uploads.tgz",
        "-C",
        "/data",
        ".",
    ]


def test_restore_commands_require_explicit_confirmation():
    args = parse_args(["restore-db", "--input", "backups/devmemory-db.sql"])

    with pytest.raises(SystemExit, match="Refusing restore without --yes"):
        build_command(args, OpsConfig())

    args = parse_args(["restore-uploads", "--input", "backups/devmemory-uploads.tgz"])

    with pytest.raises(SystemExit, match="Refusing restore without --yes"):
        build_command(args, OpsConfig())


def test_restore_uploads_clears_volume_only_after_yes():
    args = parse_args(["restore-uploads", "--input", "backups/devmemory-uploads.tgz", "--yes"])
    command = build_command(args, OpsConfig())
    backup_dir = str(Path("backups").resolve())

    assert command == [
        "docker",
        "run",
        "--rm",
        "-v",
        "devmemory_uploads:/data",
        "-v",
        f"{backup_dir}:/backup",
        "busybox",
        "sh",
        "-c",
        "rm -rf /data/* && tar xzf /backup/devmemory-uploads.tgz -C /data",
    ]


def test_upgrade_builds_and_runs_smoke_when_requested():
    args = parse_args(["upgrade", "--smoke"])
    command = build_command(args, OpsConfig())

    assert command == [
        "docker",
        "compose",
        "--env-file",
        ".env.production",
        "-f",
        "docker-compose.prod.yml",
        "up",
        "--build",
        "-d",
    ]
    assert args.smoke is True
    assert args.smoke_base_url == "http://127.0.0.1:5173/api"


def test_rollback_checks_out_target_ref_before_restarting_stack():
    args = parse_args(["rollback", "--ref", "v1.0.0"])
    command = build_command(args, OpsConfig())

    assert command == ["git", "checkout", "v1.0.0"]
