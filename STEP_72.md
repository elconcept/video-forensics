# Step 72: automatic h265nal authority stage in every OS launcher

This step integrates the migrated parser path into the automated analysis workflow.

For every input file the launcher now invokes one migration stage. The stage:

1. identifies the primary video codec with FFprobe
2. records a clean skip for non-HEVC inputs
3. extracts a byte-preserving HEVC Annex B stream for HEVC inputs
4. invokes the pinned h265nal wrapper and semantic normalizer
5. invokes FFprobe as the independent control backend
6. optionally accepts a legacy JSON result, comparison-only
7. records whether the result may support high-weight conclusions

The output is placed inside the current timestamp at `hevc_parser_migration/`, so cross-machine and cross-timestamp comparison includes the parser-authority manifests automatically.
