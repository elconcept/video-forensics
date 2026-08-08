from video_forensics.tools.decoder_diagnostics import MISSING_REFERENCE


def test_extracts_missing_reference_poc() -> None:
    text = "[hevc] Could not find ref with POC 0\nCould not find ref with POC 43"
    assert [int(match.group(1)) for match in MISSING_REFERENCE.finditer(text)] == [0, 43]
