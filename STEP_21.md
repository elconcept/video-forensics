# Step 21: decoder-run comparison

After copying native run directories from all machines into one common directory, this tool:

- refuses comparison unless all manifests contain the same input SHA-256
- compares frame counts
- compares framemd5 hashes at each output position
- records PTS values
- reports the first position where frame presence or hashes diverge
- aggregates missing-reference POC messages and hardware-related log lines

Example native invocation:

python -m video_forensics.native.compare_decoder_runs results/1796_runs --output results/1796_comparison

Outputs:

- `decoder_matrix.json`
- `frame_comparison.csv`
