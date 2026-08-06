from pathlib import Path

path = Path("pyproject.toml")
text = path.read_text(encoding="utf-8")
entry = 'video-forensics-decoder-matrix-report = "video_forensics.native.decoder_matrix_report:main"\n'
if entry not in text:
    anchor = 'video-forensics-osd-glyph-metrics = "video_forensics.native.osd_glyph_metrics:main"\n'
    if anchor not in text:
        raise SystemExit("Cannot find OSD glyph entry point")
    text = text.replace(anchor, anchor + entry, 1)
path.write_text(text, encoding="utf-8")
