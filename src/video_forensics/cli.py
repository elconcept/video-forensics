from __future__ import annotations

import argparse

from video_forensics import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="video-forensics")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")

    analyze = sub.add_parser("analyze", help="run the forensic analysis pipeline")
    analyze.add_argument("video")
    analyze.add_argument("--output", required=True)

    sub.add_parser("tools", help="list available analytical tools")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return 0
    parser.error("repository scaffold only; analytical modules are not implemented yet")
    return 2
