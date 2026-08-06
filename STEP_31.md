# Step 31: byte-exact orphan stream builder

This step builds controlled test streams from an Annex B HEVC stream and an explicit analyst plan.

The plan supplies:

- VPS/SPS/PPS NAL numbers
- candidate IDR NAL numbers
- inclusive orphan-tail NAL range

For every candidate IDR, the builder writes:

`[selected parameters][selected IDR][orphan NAL range]`

The module validates the selected NAL types, records offsets and hashes, and preserves a complete source-to-output manifest.

It deliberately does not infer POC, RPS, or the orphan boundary. Automatic derivation requires the full SPS/PPS and slice-header parser planned for the next stage.

Apply the entry point once:

python3 pyproject.patch.py
rm pyproject.patch.py
