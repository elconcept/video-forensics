from __future__ import annotations

import os
from pathlib import Path

ROOT = Path.cwd().resolve()
PIPELINE = ROOT / "git-pipeline.sh"
CLOSER = ROOT / "scripts/close_step.py"
MAKE_CHANGELOG = ROOT / "make_changelog.py"

PIPELINE_TEXT = r'''#!/bin/bash
set -euo pipefail

REPO="/Users/tom/projects/video-forensics"
DOWNLOADS="/Users/tom/Downloads"

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 STEP_NUMBER [--finalize-current]" >&2
    exit 2
fi

STEP_NUMBER="$1"
shift

cd "$REPO"
exec python3 "$REPO/scripts/close_step.py" \
    --step "$STEP_NUMBER" \
    --repo "$REPO" \
    --downloads "$DOWNLOADS" \
    "$@"
'''

CLOSER_TEXT = r'''from __future__ import annotations

import argparse
import os
import shutil
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
    changelog.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=".CHANGE.LOG.", dir=changelog.parent, text=True
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(combined)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, changelog)
    finally:
        temporary_path.unlink(missing_ok=True)


def ensure_clean_step_inputs(repo: Path, step: int) -> tuple[Path, Path]:
    executor = repo / EXECUTOR_NAME
    step_file = repo / STEP_TEMPLATE.format(step=step)
    if not executor.is_file():
        raise FileNotFoundError(f"missing one-time executor: {executor}")
    if not step_file.is_file():
        raise FileNotFoundError(f"missing step description: {step_file}")
    return executor, step_file


def close_step(step: int, repo: Path, downloads: Path, finalize_current: bool) -> None:
    repo = repo.resolve(strict=True)
    downloads = downloads.resolve(strict=True)
    tarball = downloads / TARBALL_TEMPLATE.format(step=step)

    if not finalize_current:
        if not tarball.is_file():
            raise FileNotFoundError(f"missing tarball: {tarball}")
        if (repo / EXECUTOR_NAME).exists():
            raise FileExistsError(
                f"stale executor exists before extraction: {repo / EXECUTOR_NAME}"
            )
        extract_tarball(tarball, repo)
        tarball.unlink()
        print(f"Removed downloaded tarball: {tarball}")

    executor, step_file = ensure_clean_step_inputs(repo, step)
    run([sys.executable, str(executor)], cwd=repo)
    executor.unlink()
    print(f"Removed one-time executor: {executor}")

    prepend_changelog(step_file, repo / "CHANGE.LOG", step)
    step_file.unlink()
    print(f"Prepended {step_file.name} to CHANGE.LOG and removed the source file")

    print("=== Rozpoczynam proces aktualizacji ===")
    run(["ruff", "check", ".", "--fix", "--unsafe-fixes"], cwd=repo)
    run(["pytest"], cwd=repo)
    run(["git", "diff", "--check"], cwd=repo)
    run(["git", "add", "."], cwd=repo)
    run(["git", "commit", "-m", "Next Step"], cwd=repo)
    run(["git", "push"], cwd=repo)
    print("=== Gotowe! Nowy krok został opublikowany. ===")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", required=True, type=int)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--downloads", required=True, type=Path)
    parser.add_argument("--finalize-current", action="store_true")
    args = parser.parse_args()
    try:
        close_step(
            args.step,
            args.repo,
            args.downloads,
            args.finalize_current,
        )
    except (
        FileExistsError,
        FileNotFoundError,
        OSError,
        subprocess.CalledProcessError,
        tarfile.TarError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

MAKE_CHANGELOG_TEXT = r'''from __future__ import annotations

import sys

MESSAGE = (
    "make_changelog.py is retired. Use ./git-pipeline.sh STEP_NUMBER; "
    "the step closer prepends exactly one STEP_<n>.md atomically."
)


def main() -> int:
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
'''

PIPELINE.write_text(PIPELINE_TEXT, encoding="utf-8")
os.chmod(PIPELINE, 0o755)
CLOSER.parent.mkdir(parents=True, exist_ok=True)
CLOSER.write_text(CLOSER_TEXT, encoding="utf-8")
MAKE_CHANGELOG.write_text(MAKE_CHANGELOG_TEXT, encoding="utf-8")

for path in (CLOSER, MAKE_CHANGELOG):
    compile(path.read_text(encoding="utf-8"), str(path), "exec")

print("Installed unified step closer.")
