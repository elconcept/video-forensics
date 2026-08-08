from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path.cwd()
POC = ROOT / "src/video_forensics/tools/hevc_poc.py"
MODELS = ROOT / "src/video_forensics/tools/hevc_models.py"
TEST = ROOT / "tests/test_hevc_models.py"
MOVED = ("BitReader", "SPS", "PPS")


def source_segment(text: str, node: ast.AST) -> str:
    lines = text.splitlines(keepends=True)
    start = node.lineno - 1
    end = node.end_lineno
    return "".join(lines[start:end]).rstrip() + "\n"


def find_classes(tree: ast.Module) -> dict[str, ast.ClassDef]:
    found = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name in MOVED
    }
    missing = sorted(set(MOVED) - set(found))
    if missing:
        raise SystemExit("Brak klas w hevc_poc.py: " + ", ".join(missing))
    return found


def imported_names(tree: ast.Module) -> dict[str, str]:
    result: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            segment = ast.unparse(node)
            for alias in node.names:
                result[alias.asname or alias.name.split(".")[0]] = segment
        elif isinstance(node, ast.ImportFrom):
            segment = ast.unparse(node)
            for alias in node.names:
                result[alias.asname or alias.name] = segment
    return result


def class_dependencies(classes: dict[str, ast.ClassDef]) -> set[str]:
    names: set[str] = set()
    for node in classes.values():
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                names.add(child.id)
    return names - set(MOVED) - set(dir(__builtins__))


def rewrite_poc(text: str, classes: dict[str, ast.ClassDef]) -> str:
    lines = text.splitlines(keepends=True)
    ranges = sorted(
        ((node.lineno - 1, node.end_lineno) for node in classes.values()),
        reverse=True,
    )
    for start, end in ranges:
        del lines[start:end]
    rewritten = "".join(lines)
    import_line = "from video_forensics.tools.hevc_models import BitReader, PPS, SPS\n"
    if import_line not in rewritten:
        future = "from __future__ import annotations\n"
        if future in rewritten:
            rewritten = rewritten.replace(future, future + "\n" + import_line, 1)
        else:
            rewritten = import_line + rewritten
    return rewritten


def rewrite_consumer(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^from video_forensics\.tools\.hevc_poc import (?P<names>[^\n]+)$",
        re.MULTILINE,
    )
    changed = False

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        raw = match.group("names")
        if "(" in raw or "\\" in raw:
            raise SystemExit(f"Nieobsługiwany wielowierszowy import w {path}: {raw}")
        names = [name.strip() for name in raw.split(",")]
        moved = [name for name in names if name.split(" as ")[0] in MOVED]
        retained = [name for name in names if name.split(" as ")[0] not in MOVED]
        if not moved:
            return match.group(0)
        changed = True
        output = [
            "from video_forensics.tools.hevc_models import " + ", ".join(moved)
        ]
        if retained:
            output.append(
                "from video_forensics.tools.hevc_poc import " + ", ".join(retained)
            )
        return "\n".join(output)

    rewritten = pattern.sub(replace, text)
    if changed:
        path.write_text(rewritten, encoding="utf-8")
    return changed


def main() -> None:
    if not POC.is_file():
        raise SystemExit(f"Brak pliku: {POC}")
    if MODELS.exists():
        raise SystemExit(f"Plik docelowy już istnieje: {MODELS}")

    text = POC.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(POC))
    classes = find_classes(tree)
    imports = imported_names(tree)
    dependencies = class_dependencies(classes)
    unresolved = sorted(name for name in dependencies if name not in imports)
    if unresolved:
        raise SystemExit(
            "Klasy modeli zależą od lokalnych symboli, których executor nie przenosi: "
            + ", ".join(unresolved)
        )

    import_lines = sorted({imports[name] for name in dependencies})
    model_text = "from __future__ import annotations\n\n"
    if import_lines:
        model_text += "\n".join(import_lines) + "\n\n"
    model_text += "\n\n".join(
        source_segment(text, classes[name]).rstrip() for name in MOVED
    ) + "\n"
    compile(model_text, str(MODELS), "exec")
    MODELS.write_text(model_text, encoding="utf-8")

    rewritten_poc = rewrite_poc(text, classes)
    compile(rewritten_poc, str(POC), "exec")
    POC.write_text(rewritten_poc, encoding="utf-8")

    changed: list[str] = []
    for base in (ROOT / "src", ROOT / "tests"):
        for path in sorted(base.rglob("*.py")):
            if path == POC:
                continue
            if rewrite_consumer(path):
                changed.append(str(path.relative_to(ROOT)))

    TEST.write_text(
        '''from __future__ import annotations\n\nfrom video_forensics.tools.hevc_models import BitReader, PPS, SPS\nfrom video_forensics.tools import hevc_poc\n\n\ndef test_hevc_poc_reexports_neutral_models() -> None:\n    assert hevc_poc.BitReader is BitReader\n    assert hevc_poc.SPS is SPS\n    assert hevc_poc.PPS is PPS\n\n\ndef test_bit_reader_remains_operational() -> None:\n    reader = BitReader(bytes([0b10100000]))\n    assert reader.bit() == 1\n    assert reader.bits(2) == 1\n''',
        encoding="utf-8",
    )

    for path in (MODELS, POC, TEST):
        compile(path.read_text(encoding="utf-8"), str(path), "exec")

    remaining = []
    for base in (ROOT / "src", ROOT / "tests"):
        for path in base.rglob("*.py"):
            if path == POC:
                continue
            content = path.read_text(encoding="utf-8")
            if re.search(
                r"from video_forensics\.tools\.hevc_poc import .*\b(?:BitReader|SPS|PPS)\b",
                content,
            ):
                remaining.append(str(path.relative_to(ROOT)))
    if remaining:
        raise SystemExit("Pozostały importy modeli z hevc_poc: " + ", ".join(remaining))

    print("Step 86 integrated.")
    print("Neutral model module: src/video_forensics/tools/hevc_models.py")
    print("Rewritten consumers:")
    for path in changed:
        print(f"- {path}")


if __name__ == "__main__":
    main()
