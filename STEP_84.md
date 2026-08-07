# Step 84: guarded removal of the legacy HEVC parser

The real `1796.mp4` regression gate passed with:

- verified source SHA-256
- successful FFmpeg control
- zero field mismatches
- 252 comparable records
- semantic agreement
- complete applicable RPS comparison

This finalizer removes the legacy SPS, PPS and POC parser modules only after independently validating the persisted regression gate. It also removes the comparison exporter and legacy-specific tests, disconnects the exporter from the migration stage, removes its entrypoint, and archives the passing gate under `config/hevc_migration_evidence/`.

The h265nal primary path and FFmpeg control path remain in place. The finalizer refuses to run if any required check is absent or failed.
