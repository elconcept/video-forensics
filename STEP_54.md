# Step 54: first and dependent HEVC slice-segment headers

This step adds structural handling of every VCL slice segment, not only the first segment of a picture.

It parses and records:

- `first_slice_segment_in_pic_flag`
- `no_output_of_prior_pics_flag` for IRAP NAL units
- PPS identifier
- `dependent_slice_segment_flag`
- `slice_segment_address` using SPS-derived CTB geometry
- extra slice-header bits
- slice type
- picture-output flag
- colour-plane identifier
- POC LSB for non-IDR independent segments
- header bit and byte coverage

Dependent segments inherit the independent segment fields of the same picture and record the source NAL number. A dependent segment without a preceding independent segment produces a high-severity structural finding.

Outputs: `slice_segments.json` and `slice_segments.csv`.
