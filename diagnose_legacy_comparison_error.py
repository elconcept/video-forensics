from __future__ import annotations

from pathlib import Path

MESSAGE = "comparison was produced without legacy backend"
ROOT = Path.cwd()
SKIP = {".git", ".venv", "build", "dist", "work", "__pycache__"}

matches: list[tuple[Path, int, list[str]]] = []
for path in ROOT.rglob("*.py"):
    if any(part in SKIP for part in path.relative_to(ROOT).parts):
        continue
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        continue
    for index, line in enumerate(lines):
        if MESSAGE in line:
            start = max(0, index - 15)
            end = min(len(lines), index + 16)
            matches.append((path, index + 1, lines[start:end]))

output = Path("legacy_comparison_error_context.txt")
with output.open("w", encoding="utf-8") as handle:
    if not matches:
        handle.write(f"Nie znaleziono tekstu: {MESSAGE!r}\n")
    for path, line_number, context in matches:
        handle.write(f"FILE: {path}\nLINE: {line_number}\n")
        context_start = max(1, line_number - 15)
        for offset, line in enumerate(context, start=context_start):
            marker = ">>>" if offset == line_number else "   "
            handle.write(f"{marker} {offset:5d}: {line}\n")
        handle.write("\n")

print(output)
