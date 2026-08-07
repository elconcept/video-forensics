from __future__ import annotations

import ast
import json
from pathlib import Path

FILES = [
    Path("src/video_forensics/tools/hevc_bitstream.py"),
    Path("src/video_forensics/tools/hevc_sps.py"),
    Path("src/video_forensics/tools/hevc_pps.py"),
    Path("src/video_forensics/tools/hevc_poc.py"),
]


def literal(node: ast.AST | None):
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return ast.unparse(node)


def inspect(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {"path": str(path), "present": False}
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    functions = []
    classes = []
    argparse_calls = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                {
                    "name": node.name,
                    "arguments": [arg.arg for arg in node.args.args],
                    "keyword_only": [arg.arg for arg in node.args.kwonlyargs],
                    "returns": ast.unparse(node.returns) if node.returns else None,
                    "line": node.lineno,
                }
            )
        elif isinstance(node, ast.ClassDef):
            classes.append({"name": node.name, "line": node.lineno})
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"add_argument", "set_defaults"}
        ):
            argparse_calls.append(
                {
                    "method": node.func.attr,
                    "args": [literal(arg) for arg in node.args],
                    "kwargs": {
                        keyword.arg: literal(keyword.value)
                        for keyword in node.keywords
                        if keyword.arg
                    },
                    "line": node.lineno,
                }
                )
    return {
        "path": str(path),
        "present": True,
        "functions": sorted(functions, key=lambda item: int(item["line"])),
        "classes": sorted(classes, key=lambda item: int(item["line"])),
        "argparse": sorted(argparse_calls, key=lambda item: int(item["line"])),
    }


result = {"files": [inspect(path) for path in FILES]}
output = Path("work/results/hevc_legacy_entrypoints.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(output)
