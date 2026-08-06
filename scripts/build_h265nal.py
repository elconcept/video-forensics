from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

DEFAULT_REPOSITORY = "https://github.com/chemag/h265nal.git"
DEFAULT_REVISION = "e5f8a3b"


def execute(argv: list[str], cwd: Path | None = None) -> None:
    subprocess.run(argv, cwd=cwd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("third_party/h265nal"))
    parser.add_argument("--build", type=Path, default=Path("build/h265nal"))
    parser.add_argument("--install", type=Path, default=Path(".local/h265nal"))
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    args = parser.parse_args()

    for tool in ("git", "cmake"):
        if shutil.which(tool) is None:
            raise SystemExit(f"missing required build tool: {tool}")

    source = args.source.resolve()
    build = args.build.resolve()
    install = args.install.resolve()
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        execute(["git", "clone", "--no-checkout", args.repository, str(source)])
    execute(["git", "fetch", "--tags", "origin"], cwd=source)
    execute(["git", "checkout", "--detach", args.revision], cwd=source)
    resolved_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    build.mkdir(parents=True, exist_ok=True)
    execute(
        [
            "cmake",
            "-S",
            str(source),
            "-B",
            str(build),
            "-DCMAKE_BUILD_TYPE=Release",
            "-DBUILD_H265_TESTS=OFF",
            "-DBUILD_CLANG_FUZZER=OFF",
        ]
    )
    execute(["cmake", "--build", str(build), "--config", "Release"])

    candidates = [
        build / "tools" / "h265nal",
        build / "tools" / "Release" / "h265nal.exe",
        build / "Release" / "h265nal.exe",
    ]
    binary = next((path for path in candidates if path.is_file()), None)
    if binary is None:
        raise SystemExit("h265nal binary was not produced in an expected location")
    install.mkdir(parents=True, exist_ok=True)
    target = install / binary.name
    shutil.copy2(binary, target)
    manifest = {
        "repository": args.repository,
        "requested_revision": args.revision,
        "resolved_revision": resolved_revision,
        "binary": str(target),
    }
    (install / "build_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
