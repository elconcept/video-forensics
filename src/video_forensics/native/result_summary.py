from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SKIP_NAMES = {"human_summary.json"}


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def discover(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    results: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(root.rglob("*.json")):
        if path.name in SKIP_NAMES:
            continue
        payload = read_json(path)
        if payload is not None:
            results.append((path, payload))
    return results


def module_name(path: Path, payload: dict[str, Any]) -> str:
    return str(payload.get("module") or path.stem)


def status(payload: dict[str, Any]) -> str:
    value = payload.get("status")
    if value is not None:
        return str(value)
    summary = payload.get("summary")
    if isinstance(summary, dict) and summary.get("failed"):
        return "completed_with_failures"
    return "completed"


def collect_findings(payload: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        findings = payload.get("findings")
        if isinstance(findings, list):
            found.extend(item for item in findings if isinstance(item, dict))
        for key, value in payload.items():
            if key != "findings" and isinstance(value, (dict, list)):
                found.extend(collect_findings(value))
    elif isinstance(payload, list):
        for value in payload:
            if isinstance(value, (dict, list)):
                found.extend(collect_findings(value))
    return found


def compact_metrics(payload: dict[str, Any]) -> list[tuple[str, object]]:
    accepted = (
        "frame_count",
        "picture_count",
        "pair_count",
        "variant_count",
        "decoder_count",
        "finding_count",
        "parsed_count",
        "series_count",
        "review_asset_count",
        "email_frame_count",
        "mapped_pts_count",
        "poc_regression_count",
        "dependent_slice_segment_count",
        "slice_segment_error_count",
    )
    metrics: list[tuple[str, object]] = []
    for key in accepted:
        if key in payload and isinstance(payload[key], (int, float, str, bool)):
            metrics.append((key, payload[key]))
    summary = payload.get("summary")
    if isinstance(summary, dict):
        for key, value in summary.items():
            if isinstance(value, (int, float, str, bool)):
                metrics.append((f"summary.{key}", value))
    return metrics[:12]


def source_identity(documents: list[tuple[Path, dict[str, Any]]]) -> dict[str, str]:
    for _, payload in documents:
        candidate = payload.get("input") or payload.get("source")
        if isinstance(candidate, dict):
            path = candidate.get("path")
            digest = candidate.get("sha256")
            if path or digest:
                return {
                    "path": "" if path is None else str(path),
                    "sha256": "" if digest is None else str(digest),
                }
    return {"path": "", "sha256": ""}


def finding_key(finding: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(finding.get("id", "UNNAMED_FINDING")),
        str(finding.get("severity", "unspecified")),
        str(finding.get("description", "")),
    )


def unique_findings(documents: list[tuple[Path, dict[str, Any]]]) -> list[dict[str, Any]]:
    unique: dict[tuple[str, str, str], dict[str, Any]] = {}
    for path, payload in documents:
        for finding in collect_findings(payload):
            key = finding_key(finding)
            item = dict(finding)
            item.setdefault("source_files", [])
            item["source_files"].append(str(path))
            if key in unique:
                unique[key]["source_files"].append(str(path))
            else:
                unique[key] = item
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unspecified": 4}
    return sorted(
        unique.values(),
        key=lambda item: (
            order.get(str(item.get("severity", "unspecified")).lower(), 5),
            str(item.get("id", "")),
        ),
    )


def render(root: Path, documents: list[tuple[Path, dict[str, Any]]]) -> str:
    identity = source_identity(documents)
    findings = unique_findings(documents)
    statuses = Counter(status(payload) for _, payload in documents)
    modules = [(path, module_name(path, payload), status(payload), payload) for path, payload in documents]

    lines = [
        "# Podsumowanie analizy",
        "",
        f"- Katalog wyników: `{root}`",
        f"- Wygenerowano UTC: `{datetime.now(UTC).isoformat()}`",
        f"- Plik źródłowy: `{identity['path'] or 'brak w manifestach'}`",
        f"- SHA-256 źródła: `{identity['sha256'] or 'brak w manifestach'}`",
        f"- Odczytane dokumenty JSON: `{len(documents)}`",
        f"- Unikalne ustalenia: `{len(findings)}`",
        "",
        "## Stan wykonania",
        "",
    ]
    for name, count in sorted(statuses.items()):
        lines.append(f"- `{name}`: {count}")

    lines.extend(["", "## Ustalenia", ""])
    if not findings:
        lines.append("Nie znaleziono strukturalnych ustaleń w dostępnych wynikach.")
    else:
        for finding in findings:
            identifier = finding.get("id", "UNNAMED_FINDING")
            severity = finding.get("severity", "unspecified")
            description = finding.get("description", "Brak opisu.")
            lines.extend(
                [
                    f"### {identifier}",
                    "",
                    f"- Waga: `{severity}`",
                    f"- Opis: {description}",
                ]
            )
            observations = finding.get("observations")
            if observations is not None:
                serialized = json.dumps(observations, ensure_ascii=False, sort_keys=True)
                if len(serialized) > 1200:
                    serialized = serialized[:1200] + "…"
                lines.append(f"- Obserwacje: `{serialized}`")
            boundary = finding.get("interpretation_boundary")
            if boundary:
                lines.append(f"- Granica interpretacji: {boundary}")
            sources = finding.get("source_files", [])
            if sources:
                relative = [str(Path(value).relative_to(root)) for value in sources]
                lines.append("- Źródła: " + ", ".join(f"`{value}`" for value in sorted(set(relative))))
            lines.append("")

    lines.extend(["## Wyniki modułów", ""])
    for path, name, module_status, payload in modules:
        relative = path.relative_to(root)
        lines.extend(
            [
                f"### {name}",
                "",
                f"- Status: `{module_status}`",
                f"- Manifest: `{relative}`",
            ]
        )
        for key, value in compact_metrics(payload):
            lines.append(f"- {key}: `{value}`")
        boundary = payload.get("interpretation_boundary")
        if boundary:
            lines.append(f"- Granica interpretacji: {boundary}")
        lines.append("")

    lines.extend(
        [
            "## Pliki wynikowe",
            "",
            "Pełne dane, logi, tabele CSV, obrazy i manifesty pozostają w podkatalogach tego katalogu. Niniejszy plik jest indeksem czytelnym dla człowieka i nie zastępuje danych źródłowych modułów.",
            "",
        ]
    )
    return "\n".join(lines)


def create_summary(root: Path, output_name: str = "SUMMARY.md") -> Path:
    root = root.expanduser().resolve(strict=True)
    documents = discover(root)
    output = root / output_name
    output.write_text(render(root, documents), encoding="utf-8", newline="\n")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-result-summary")
    parser.add_argument("results_root", type=Path)
    parser.add_argument("--output-name", default="SUMMARY.md")
    args = parser.parse_args()
    try:
        output = create_summary(args.results_root, args.output_name)
    except (FileNotFoundError, OSError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"summary": str(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
