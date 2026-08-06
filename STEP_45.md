# Step 45: HEVC SPS/PPS, first-slice POC, and regression detection

This step extends `hevc_bitstream` with:

- RBSP emulation-prevention removal
- early SPS parsing through `log2_max_pic_order_cnt_lsb_minus4`
- early PPS parsing required by first-slice headers
- first-slice POC LSB extraction
- HEVC POC MSB wrap derivation
- detection of POC regression at a non-IRAP picture
- picture-level CSV output with NAL number and byte offset
- a review-required orphan-pipeline plan draft

The generated plan is intentionally marked `draft_requires_review`. The parser does not yet derive the complete reference-picture set, so the plan must not be executed without checking the selected parameter sets, IDRs, orphan boundary, and parse-error list.

Apply integration once:

python3 hevc_bitstream.patch.py
rm hevc_bitstream.patch.py
