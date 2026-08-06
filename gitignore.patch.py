from pathlib import Path

path = Path(".gitignore")
text = path.read_text(encoding="utf-8") if path.exists() else ""
block = """
# Local evidence and generated analysis results
work/evidence/*
!work/evidence/.gitkeep
work/results/*
!work/results/.gitkeep
""".lstrip()
if "work/evidence/*" not in text:
    if text and not text.endswith("\n"):
        text += "\n"
    text += "\n" + block
path.write_text(text, encoding="utf-8")
