# Step 43: OSD glyph geometry screening

This step adds connected-component measurements for pre-cropped burned-in timestamp images.

It records per frame:

- connected-component count
- bounding boxes
- component baselines
- glyph-height ranges
- aggregate baseline, height, and width ranges

Findings are low-severity and require reference material. The module does not identify a font or conclude that an overlay was altered. Punctuation, anti-aliasing, crop geometry, threshold selection, and natural character-shape differences are retained as ordinary explanations.

Apply the entry point once:

python3 pyproject.patch.py
rm pyproject.patch.py
