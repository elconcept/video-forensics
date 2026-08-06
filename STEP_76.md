# Step 76: executable reference-file regression gate

This step turns the remaining real-reference comparison into a repeatable acceptance gate.

A configuration identifies each verified source by path and SHA-256 and points to its completed `reference_comparison.json`. For every case the gate checks:

- source identity
- successful FFmpeg control
- maximum permitted semantic field mismatches
- minimum comparable record count
- legacy semantic agreement when required
- complete short-term and long-term RPS comparison when required

The command exits with status 1 on an unmet acceptance criterion. `legacy_removal_ready` becomes true only when every configured reference case passes. The example configuration contains placeholders and is not treated as evidence until replaced with a verified source hash and real comparison path.
