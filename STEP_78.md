# Step 78: automatic discovery of the comparison-only legacy result

This step removes the need to manually pass a legacy JSON path after each baseline run.

The discovery module scans the current timestamp directory, excludes migrated h265nal outputs, scores only JSON objects that expose NAL or SPS/PPS/slice collections, and selects a result only when there is one unambiguous highest-scoring candidate. Equal top candidates are reported as ambiguous and are never silently chosen.

Linux and macOS launchers now discover the baseline legacy result before invoking the HEVC migration stage. If no candidate exists, h265nal and FFmpeg still run, but legacy agreement and removal readiness remain false. The legacy parser remains comparison-only.
