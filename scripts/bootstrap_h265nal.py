from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

UPSTREAM = "https://github.com/chemag/h265nal.git"
PINNED_REF = "e5f8a3b"


def command(argv: list[str], cwd: Path | None = None) -> str:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "command failed: " + " ".join(argv))
    return completed.stdout.strip()


def require_build_tools() -> dict[str, str]:
    tools = {"git": shutil.which("git"), "cmake": shutil.which("cmake")}
    compiler = shutil.which("c++") or shutil.which("clang++") or shutil.which("g++") or shutil.which("cl")
    tools["compiler"] = compiler
    missing = [name for name, path in tools.items() if not path]
    if missing:
        raise FileNotFoundError("missing build tools: " + ", ".join(missing))
    return {name: str(path) for name, path in tools.items()}


def ensure_source(root: Path) -> tuple[Path, str]:
    destination = root / "third_party/h265nal"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        command(["git", "clone", "--no-checkout", UPSTREAM, str(destination)])
    if not (destination / ".git").exists():
        raise ValueError(f"existing path is not a git checkout: {destination}")
    command(["git", "remote", "set-url", "origin", UPSTREAM], destination)
    command(["git", "fetch", "--depth", "1", "origin", PINNED_REF], destination)
    commit = command(["git", "rev-parse", "FETCH_HEAD^{commit}"], destination)
    if len(commit) != 40:
        raise ValueError(f"resolved h265nal commit is not full SHA-1: {commit}")
    command(["git", "checkout", "--detach", commit], destination)
    actual = command(["git", "rev-parse", "HEAD"], destination)
    if actual != commit:
        raise RuntimeError("h265nal checkout does not match resolved commit")
    return destination, commit


def build(root: Path, source: Path) -> tuple[Path, Path]:
    build_dir = root / "build/h265nal"
    command(
        [
            "cmake",
            "-S",
            str(source),
            "-B",
            str(build_dir),
            "-DCMAKE_BUILD_TYPE=Release",
            "-DBUILD_H265_TESTS=OFF",
            "-DBUILD_CLANG_FUZZER=OFF",
        ]
    )
    command(["cmake", "--build", str(build_dir), "--config", "Release"])
    candidates = [
        build_dir / "tools/h265nal",
        build_dir / "tools/h265nal.exe",
        build_dir / "tools/Release/h265nal.exe",
        build_dir / "Release/h265nal.exe",
    ]
    binary = next((path for path in candidates if path.is_file()), None)
    if binary is None:
        raise FileNotFoundError("built h265nal binary not found")

    wrapper_source = root / "native/h265nal_json_wrapper"
    wrapper_build = root / "build/h265nal_json_wrapper"
    command([
        "cmake", "-S", str(wrapper_source), "-B", str(wrapper_build),
        "-DCMAKE_BUILD_TYPE=Release",
    ])
    command(["cmake", "--build", str(wrapper_build), "--config", "Release"])
    wrapper_candidates = [
        wrapper_build / "bin/h265nal_json_wrapper",
        wrapper_build / "bin/h265nal_json_wrapper.exe",
        wrapper_build / "bin/Release/h265nal_json_wrapper.exe",
        wrapper_build / "Release/h265nal_json_wrapper.exe",
    ]
    wrapper = next((item for item in wrapper_candidates if item.is_file()), None)
    if wrapper is None:
        raise FileNotFoundError("built h265nal JSON wrapper not found")
    return binary.resolve(), wrapper.resolve()


def bootstrap(repository: Path) -> dict[str, object]:
    repository = repository.expanduser().resolve(strict=True)
    tools = require_build_tools()
    source, commit = ensure_source(repository)
    binary, wrapper = build(repository, source)
    lock = {
        "schema_version": 1,
        "upstream": UPSTREAM,
        "requested_ref": PINNED_REF,
        "commit": commit,
        "source": str(source),
        "binary": str(binary),
        "json_wrapper": str(wrapper),
        "tools": tools,
    }
    lock_path = repository / "third_party/h265nal.lock.json"
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return lock


def main() -> int:
    parser = argparse.ArgumentParser(prog="bootstrap-h265nal")
    parser.add_argument("--repository", type=Path, default=Path("."))
    args = parser.parse_args()
    try:
        lock = bootstrap(args.repository)
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(lock, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
