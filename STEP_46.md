# Step 46: decoder-matrix reporting hierarchy

This step promotes cross-decoder disagreement from raw comparison tables into structured findings.

It emits distinct records for:

- different frame counts across decoder paths, severity high
- missing-reference diagnostics, severity high
- first exact frame-presence or checksum divergence, severity high
- pairwise normalized visual divergence, severity medium

Frame-count divergence is emitted as its own leading finding with decoder groups, minimum and maximum counts, and the count range. Perceptual comparison can be attached only when its recorded input SHA-256 matches the matrix input.

The report does not claim that one decoder output is correct, and agreement is not converted into an authenticity conclusion.
