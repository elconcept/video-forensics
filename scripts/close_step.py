from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

TARBALL_TEMPLATE = "video-forensics-step-{step}.tar.gz"
EXECUTOR_NAME = "integrate_step.py"
STEP_TEMPLATE = "STEP_{step}.md"


def run(argv: list[str], *, cwd: Path) -> None:
    print("+", " ".join(argv), flush=True)
    subprocess.run(argv, cwd=cwd, check=True)


def validate_member(member: tarfile.TarInfo) -> None:
    path = PurePosixPath(member.name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe tar member path: {member.name}")
    if member.issym() or member.islnk() or member.isdev():
        raise ValueError(f"unsupported tar member type: {member.name}")


def extract_tarball(tarball: Path, repo: Path) -> None:
    with tarfile.open(tarball, "r:gz") as archive:
        members = archive.getmembers()
        if not members:
            raise ValueError("tarball is empty")
        for member in members:
            validate_member(member)
        archive.extractall(repo, members=members, filter="data")


def prepend_changelog(step_file: Path, changelog: Path, step: int) -> None:
    content = step_file.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"{step_file.name} is empty")
    old = changelog.read_text(encoding="utf-8") if changelog.exists() else ""
    marker = f"# Step {step}:"
    if marker in old:
        raise ValueError(f"CHANGE.LOG already contains {marker}")
    combined = content + "\n\n\n" + old.lstrip("\n")
    fd, temporary = tempfile.mkstemp(prefix=".CHANGE.LOG.", dir=changelog.parent, text=True)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(combined)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, changelog)
    finally:
        temporary_path.unlink(missing_ok=True)


def close_step(step: int, repo: Path, downloads: Path, finalize_current: bool) -> None:
    repo = repo.resolve(strict=True)
    downloads = downloads.resolve(strict=True)
    tarball = downloads / TARBALL_TEMPLATE.format(step=step)

    if not finalize_current:
        if not tarball.is_file():
            raise FileNotFoundError(f"missing tarball: {tarball}")
        if (repo / EXECUTOR_NAME).exists():
            raise FileExistsError(f"stale executor exists: {repo / EXECUTOR_NAME}")
        extract_tarball(tarball, repo)
        tarball.unlink()

    executor = repo / EXECUTOR_NAME
    step_file = repo / STEP_TEMPLATE.format(step=step)
    if executor.is_file():
        run([sys.executable, str(executor)], cwd=repo)
        executor.unlink()
    elif not finalize_current:
        raise FileNotFoundError(f"missing one-time executor: {executor}")

    if step_file.is_file():
        prepend_changelog(step_file, repo / "CHANGE.LOG", step)
        step_file.unlink()
    elif not finalize_current:
        raise FileNotFoundError(f"missing step description: {step_file}")

    venv_python = repo / ".venv/bin/python"
    if not venv_python.is_file():
        raise FileNotFoundError(f"missing project virtualenv Python: {venv_python}")
    run([str(venv_python), "-m", "pip", "install", "-e", ".[dev]"], cwd=repo)
    run([str(venv_python), "-m", "ruff", "check", ".", "--fix", "--unsafe-fixes"], cwd=repo)
    run([str(venv_python), "-m", "pytest"], cwd=repo)
    run(["git", "diff", "--check"], cwd=repo)
    run(["git", "add", "."], cwd=repo)
    run(["git", "commit", "-m", "Next Step"], cwd=repo)
    run(["git", "push"], cwd=repo)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", required=True, type=int)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--downloads", required=True, type=Path)
    parser.add_argument("--finalize-current", action="store_true")
    args = parser.parse_args()
    try:
        close_step(args.step, args.repo, args.downloads, args.finalize_current)
    except (FileExistsError, FileNotFoundError, OSError, subprocess.CalledProcessError, tarfile.TarError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
