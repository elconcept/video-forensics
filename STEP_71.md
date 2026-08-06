# Step 71: h265nal primary authority pipeline with FFmpeg control

This step makes h265nal the explicit primary parser in a complete executable path.

The command:

1. reads h265nal and wrapper paths from the pinned lock file
2. invokes the C++ JSON wrapper
3. normalizes the h265nal semantic output
4. invokes FFprobe as an independent control backend
5. optionally imports a legacy JSON result for comparison only
6. compares primary and legacy NAL counts and type sequences
7. emits an authority decision for high-weight conclusions

Outputs:

- `h265nal_wrapper.json`
- `h265nal_normalized.json`
- `ffprobe_control.json`
- `parser_authority.json`

The high-weight authority flag is false unless the independent control backend completes successfully. FFprobe supports machine-readable JSON and packet-level inspection. citeturn131search328turn131search330turn131search331
