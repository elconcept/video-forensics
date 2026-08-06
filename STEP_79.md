# Step 79: one-command real reference execution for 1796.mp4

This step adds a single orchestration command for the available reference candidate `work/evidence/1796.mp4`.

It runs the normal Linux launcher, locates the newest timestamped reference comparison for the file, enrolls that concrete result with a computed SHA-256, runs the migration regression gate, and writes complete logs plus `reference_run.json`.

The command fails at the exact stage that first fails. It does not enroll a result if the launcher or comparison failed, and it does not report legacy removal readiness unless the regression gate passes.
