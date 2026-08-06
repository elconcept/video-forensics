# Step 73: field-level semantic comparison for SPS, PPS and slices

This step expands backend comparison beyond NAL counts and type sequences.

It flattens normalized h265nal SPS, PPS and slice payloads, imports legacy records strictly as comparison-only data, and compares every shared field value. It also parses FFmpeg `trace_headers` output into a separate control record.

The result records comparable-field counts, exact mismatches, missing records, legacy semantic agreement, FFmpeg control availability, and the high-weight authority gate. FFmpeg control is not treated as a replacement for the primary parser.
