from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

TOKEN = re.compile(r"0x[0-9a-fA-F]+|-?\d+|[A-Za-z_][A-Za-z0-9_]*|[{}:]")


def scalar(token: str) -> int | str:
    if token.startswith("0x"):
        return int(token, 16)
    if re.fullmatch(r"-?\d+", token):
        return int(token)
    return token


def add_field(target: dict[str, Any], key: str, value: Any) -> None:
    if key not in target:
        target[key] = value
    elif isinstance(target[key], list):
        target[key].append(value)
    else:
        target[key] = [target[key], value]


def parse_object(tokens: list[str], position: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    values: list[int | str] = []
    while position < len(tokens):
        token = tokens[position]
        if token == "}":
            if values:
                result["_values"] = values
            return result, position + 1
        if token in {"{", ":"}:
            raise ValueError(f"unexpected token {token!r} at {position}")
        if position + 1 < len(tokens) and tokens[position + 1] == ":":
            if position + 2 >= len(tokens):
                raise ValueError(f"missing value for {token}")
            add_field(result, token, scalar(tokens[position + 2]))
            position += 3
            continue
        if position + 1 < len(tokens) and tokens[position + 1] == "{":
            child, position = parse_object(tokens, position + 2)
            add_field(result, token, child)
            continue
        values.append(scalar(token))
        position += 1
    raise ValueError("unterminated h265nal object")


def parse_text(text: str) -> list[dict[str, Any]]:
    tokens = TOKEN.findall(text)
    objects: list[dict[str, Any]] = []
    position = 0
    while position < len(tokens):
        name = tokens[position]
        if position + 1 >= len(tokens) or tokens[position + 1] != "{":
            position += 1
            continue
        value, position = parse_object(tokens, position + 2)
        objects.append({"type": name, "value": value})
    return objects


def first(value: Any) -> Any:
    return value[0] if isinstance(value, list) and value else value


def normalized_nal(number: int, item: dict[str, Any]) -> dict[str, Any]:
    root = item["value"]
    header = first(root.get("nal_unit_header", {}))
    payload = first(root.get("nal_unit_payload", {}))
    nal_type = header.get("nal_unit_type") if isinstance(header, dict) else None
    return {
        "nal_number": number,
        "offset": root.get("offset"),
        "length": root.get("length"),
        "nal_unit_type": nal_type,
        "nuh_layer_id": header.get("nuh_layer_id") if isinstance(header, dict) else None,
        "nuh_temporal_id_plus1": header.get("nuh_temporal_id_plus1") if isinstance(header, dict) else None,
        "header": header,
        "payload": payload,
    }


def normalize(wrapper: dict[str, Any]) -> dict[str, object]:
    if wrapper.get("backend") != "h265nal":
        raise ValueError("wrapper backend is not h265nal")
    if not wrapper.get("success"):
        raise ValueError("h265nal wrapper did not report success")
    parsed = parse_text(str(wrapper.get("stdout", "")))
    nals = [
        normalized_nal(index, item)
        for index, item in enumerate(
            (item for item in parsed if item["type"] == "nal_unit"), start=1
        )
    ]
    if not nals:
        raise ValueError("h265nal output contains no nal_unit objects")
    return {
        "schema_version": 1,
        "module": "h265nal_normalizer",
        "primary_backend": "h265nal",
        "input": wrapper.get("input"),
        "nal_count": len(nals),
        "nal_units": nals,
        "raw_object_count": len(parsed),
        "transport_contract": wrapper.get("command_contract"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-normalize-h265nal")
    parser.add_argument("wrapper_json", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        wrapper = json.loads(args.wrapper_json.read_text(encoding="utf-8"))
        if not isinstance(wrapper, dict):
            raise TypeError("wrapper JSON must be an object")
        result = normalize(wrapper)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"nal_count": result["nal_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
