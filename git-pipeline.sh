ruff check . --fix  --unsafe-fixes
pytest
git diff --check
git add .
git commit -m "Next Step"
git push

python3 - <<'PY'
from pathlib import Path

path = Path("pyproject.toml")
text = path.read_text(encoding="utf-8")

entries = [
 'video-forensics-decoder-matrix-report = "video_forensics.native.decoder_matrix_report:main"',
 'video-forensics-static-region-series = "video_forensics.native.static_region_series:main"',
]

marker = "[project.scripts]"
start = text.find(marker)
if start == -1:
raise SystemExit("Brak sekcji [project.scripts]")

end = text.find("\n[", start + len(marker))
if end == -1:
    end = len(text)

section = text[start:end].rstrip()
for entry in entries:
    if entry not in text:
        section += "\n" + entry

text = text[:start] + section + "\n" + text[end:].lstrip("\n")
path.write_text(text, encoding="utf-8")
PY