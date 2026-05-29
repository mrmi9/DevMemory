import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OpsConfig:
    env_file: str = ".env.production"
    compose_file: str = "docker-compose.prod.yml"
    postgres_service: str = "postgres"
    postgres_user: str = "study"
    postgres_db: str = "study"
    uploads_volume: str = "devmemory_uploads"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="DevMemory private deployment operations helper.")
    parser.add_argument("--env-file", default=".env.production")
    parser.add_argument("--compose-file", default="docker-compose.prod.yml")
    parser.add_argument("--uploads-volume", default="devmemory_uploads")

    subcommands = parser.add_subparsers(dest="command", required=True)

    backup_db = subcommands.add_parser("backup-db", help="Dump PostgreSQL to a SQL file.")
    backup_db.add_argument("--output", required=True)

    backup_uploads = subcommands.add_parser("backup-uploads", help="Archive the uploads Docker volume.")
    backup_uploads.add_argument("--output", required=True)

    restore_db = subcommands.add_parser("restore-db", help="Restore PostgreSQL from a SQL file.")
    restore_db.add_argument("--input", required=True)
    restore_db.add_argument("--yes", action="store_true")

    restore_uploads = subcommands.add_parser("restore-uploads", help="Restore uploads into the Docker volume.")
    restore_uploads.add_argument("--input", required=True)
    restore_uploads.add_argument("--yes", action="store_true")

    upgrade = subcommands.add_parser("upgrade", help="Build and start the private deployment stack.")
    upgrade.add_argument("--smoke", action="store_true")
    upgrade.add_argument("--smoke-base-url", default="http://127.0.0.1:5173/api")

    rollback = subcommands.add_parser("rollback", help="Check out a target ref before restarting the stack.")
    rollback.add_argument("--ref", required=True)
    rollback.add_argument("--smoke", action="store_true")
    rollback.add_argument("--smoke-base-url", default="http://127.0.0.1:5173/api")

    return parser.parse_args(argv)


def build_command(args, config: OpsConfig):
    config = OpsConfig(env_file=args.env_file, compose_file=args.compose_file, uploads_volume=args.uploads_volume)
    if args.command == "backup-db":
        return _compose(config) + [
            "exec",
            "-T",
            config.postgres_service,
            "pg_dump",
            "-U",
            config.postgres_user,
            "-d",
            config.postgres_db,
        ]
    if args.command == "backup-uploads":
        backup_dir, backup_name = _backup_mount(args.output)
        return [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{config.uploads_volume}:/data:ro",
            "-v",
            f"{backup_dir}:/backup",
            "busybox",
            "tar",
            "czf",
            f"/backup/{backup_name}",
            "-C",
            "/data",
            ".",
        ]
    if args.command == "restore-db":
        _require_yes(args)
        return _compose(config) + ["exec", "-T", config.postgres_service, "psql", "-U", config.postgres_user, "-d", config.postgres_db]
    if args.command == "restore-uploads":
        _require_yes(args)
        backup_dir, backup_name = _backup_mount(args.input)
        return [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{config.uploads_volume}:/data",
            "-v",
            f"{backup_dir}:/backup",
            "busybox",
            "sh",
            "-c",
            f"rm -rf /data/* && tar xzf /backup/{backup_name} -C /data",
        ]
    if args.command == "upgrade":
        return _compose(config) + ["up", "--build", "-d"]
    if args.command == "rollback":
        return ["git", "checkout", args.ref]
    raise SystemExit(f"Unknown command: {args.command}")


def execute(args, config: OpsConfig):
    command = build_command(args, config)
    if args.command == "backup-db":
        _run_to_file(command, args.output)
    elif args.command == "restore-db":
        _run_from_file(command, args.input)
    else:
        if args.command == "backup-uploads":
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(command, check=True)

    if args.command == "rollback":
        subprocess.run(_compose(config) + ["up", "--build", "-d"], check=True)

    if getattr(args, "smoke", False):
        subprocess.run([sys.executable, "scripts/smoke_test.py", "--base-url", args.smoke_base_url], check=True)


def _compose(config: OpsConfig):
    return ["docker", "compose", "--env-file", config.env_file, "-f", config.compose_file]


def _backup_mount(path_text: str):
    path = Path(path_text)
    backup_dir = str(path.parent.resolve()) if str(path.parent) != "." else str(Path(".").resolve())
    return backup_dir, path.name


def _require_yes(args):
    if not getattr(args, "yes", False):
        raise SystemExit("Refusing restore without --yes")


def _run_to_file(command, output):
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "wb") as handle:
        subprocess.run(command, stdout=handle, check=True)


def _run_from_file(command, input_path):
    with open(input_path, "rb") as handle:
        subprocess.run(command, stdin=handle, check=True)


def main(argv=None):
    args = parse_args(argv)
    execute(args, OpsConfig(env_file=args.env_file, compose_file=args.compose_file, uploads_volume=args.uploads_volume))


if __name__ == "__main__":
    main()
