# Step 49: decoder-order frame timestamps

This step removes the need to map OSD images to a generic FFprobe frame table.

For one decoder profile it runs the same decode-path arguments with FFmpeg `showinfo` and records:

- one-based exported frame number
- zero-based decoder output index
- integer PTS
- PTS in seconds
- exact decoder profile and command
- input SHA-256 and host-profile identifier

The resulting `frame_timestamps.csv` can be supplied directly to `video-forensics-osd-timeline`. It must be paired only with images exported through the same decoder profile and `-vsync 0` ordering.
