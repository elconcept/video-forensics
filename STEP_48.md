# Step 48: OSD readings mapped to frame PTS

This step adds the missing OSD table required for evidentiary review:

- frame number
- decoder-order PTS in seconds
- frame filename
- raw OCR reading
- parsed burned-in timestamp

The module accepts a frame-level CSV containing `frame_number` and either `pts_time`, `best_effort_timestamp_time`, or `pts`. It maps that table to `osd_reader.json`, reports absent PTS ranges, and separately identifies non-monotonic input PTS.

The CSV must originate from the same decoder ordering as the OSD image sequence. The module does not treat output-muxer diagnostics as source-file timestamp evidence.
