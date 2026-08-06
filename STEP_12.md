# Step 12: audio-video timeline alignment

This stage consumes the timeline and audio packet outputs. It compares calculated stream starts and ends and screens for:

- initial A/V offset
- final A/V offset
- relative drift between start and end

The thresholds are operational screening thresholds. A reported offset may arise from legitimate container or codec timing and is not proof of editing.

Apply CLI integration once:

python3 cli.patch.py
rm cli.patch.py

Outputs:

- `av_sync/findings.json`
- `av_sync/av_sync.json`
