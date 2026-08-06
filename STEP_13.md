# Step 13: optional lossless frame extraction

This stage exports decoded frames into a separate derivative directory and creates an index with SHA-256 and file size for every output image.

The default pipeline exports all frames as PNG. The implementation also supports TIFF and lossless WebP, plus explicit one-based frame ranges at the module level.

Extracted images are derivative analytical material. They do not replace the source recording or its integrity hashes.

Apply CLI integration once:

python3 cli.patch.py
rm cli.patch.py

Outputs:

- `extracted_frames/frames/`
- `extracted_frames/index.csv`
- `extracted_frames/extract_frames.json`
