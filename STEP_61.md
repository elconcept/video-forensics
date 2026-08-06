# Step 61: executable h265nal workflow and automatic bootstrap

Step 60 still did not satisfy the migration DoD. Step 61 adds one end-to-end command that accepts Annex B, discovers or builds h265nal, preserves the raw parser output, executes the primary syntax derivation, optionally compares legacy POC, and writes one workflow manifest.

All OS bootstraps now build the pinned h265nal binary when absent. A process-level integration test exercises the complete adapter and primary backend through an executable CLI fixture.

The upstream project documents Annex B parsing, stateful parameter-set handling, slice parsing, offsets, lengths, tests, fuzzing and Windows support. citeturn113search131turn112search129
