# Step 34: independent decoder verification for orphan recovery

This step compares controlled orphan-stream decodings produced by two or more decoder implementations.

Before comparison it requires:

- identical controlled variant identifiers
- identical SHA-256 values for every controlled input stream
- unique decoder output identifiers

For every decoder pair, variant, and frame it records:

- MAE
- RMSE
- luminance NCC
- identical-pixel fraction
- missing-frame status

It also summarizes minimum and mean NCC and maximum MAE for each controlled variant.

Example:

video-forensics-verify-orphan-decoders --decoder-root results/orphan_libavcodec --decoder-root results/orphan_libde265 --output results/orphan_verification

Cross-decoder agreement is reported as reconstruction reproducibility, not as an authenticity verdict.

Apply the entry point once:

python3 pyproject.patch.py
rm pyproject.patch.py
