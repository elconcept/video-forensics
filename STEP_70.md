# Step 70: semantic normalization of h265nal output

This step converts the stable wrapper envelope into the project's first native h265nal semantic schema.

The normalizer parses h265nal's nested textual objects without depending on indentation. It preserves nested header and payload structures and emits stable per-NAL records containing:

- sequential NAL number
- byte offset and length
- NAL unit type
- layer and temporal identifiers
- complete normalized header object
- complete normalized payload object

The output explicitly identifies h265nal as the primary backend. The upstream CLI documents nested `nal_unit` output with offsets, lengths, headers, parameter sets, and slice fields. citeturn130search323turn130search324
