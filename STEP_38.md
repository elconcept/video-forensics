# Step 38: independent libde265 runner

This step adds a first-class wrapper for the independent `dec265` command-line decoder.

The upstream command-line decoder accepts raw HEVC input and can write decoded YUV output with `-o`; it also accepts a worker-thread count. citeturn71search170turn71search172

The module records:

- Annex B source SHA-256
- dec265 version or help output
- complete command and logs
- decoded YUV SHA-256
- per-frame hashes and offsets
- host-profile identifier

Because raw YUV has no self-describing geometry, width, height, and pixel format are mandatory analyst-supplied parameters and are explicitly marked as such. Missing `dec265` writes an `unavailable` result rather than aborting wider analysis.

Apply the entry point once:

python3 pyproject.patch.py
rm pyproject.patch.py
