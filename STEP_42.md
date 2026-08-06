# Step 42: burned-in timestamp OCR

This step adds the first `osd_reader` implementation.

It:

- applies one explicit, fixed crop to every supplied frame
- preprocesses the crop for OCR
- invokes optional Tesseract per frame
- records the exact OCR command and diagnostic output
- emits the raw OCR string and parsed timestamp
- flags contiguous absent-reading ranges
- flags backwards timestamp movement

Tesseract is optional. If it is absent, the module writes an `unavailable` result rather than aborting broader analysis.

OCR results are machine interpretations and require visual confirmation. Glyph-baseline and typeface-consistency analysis remain a later stage.

Apply the entry point once:

python3 pyproject.patch.py
rm pyproject.patch.py
