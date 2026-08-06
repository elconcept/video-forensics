from video_forensics.cli import build_parser


def test_parser_accepts_analyze_command() -> None:
    args = build_parser().parse_args(["analyze", "input.mov", "--output", "out"])
    assert args.command == "analyze"
    assert args.video == "input.mov"
    assert args.output == "out"
