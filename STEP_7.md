# Step 7: continuity correlation

This stage consumes outputs from the timeline, GOP, and frame-metrics stages. It does not decode the video again.

It performs:

- robust metric outlier detection using median absolute deviation
- aggregation of existing timeline and GOP findings
- correlation of signals occurring on the same frame

A multi-signal candidate is a location for review, not an automatic conclusion that editing occurred.

Apply CLI integration once:

python3 cli.patch.py
rm cli.patch.py

Outputs:

- `continuity/findings.json`
- `continuity/correlations.json`
- `continuity/continuity.json`
