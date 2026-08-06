# Step 59: direct libde265 decoding of every controlled orphan variant

This step integrates `dec265` directly into `orphan_pipeline`.

After controlled streams are built, the pipeline now:

1. verifies each variant SHA-256 against `orphan_streams.json`
2. invokes `dec265` separately for every controlled reference variant
3. records the complete libde265 manifest, command, logs, raw-YUV hash, and frame inventory
4. converts each raw YUV output to lossless PNG using the declared geometry
5. writes one decoder-root manifest covering every variant
6. adds the libde265 root automatically to independent-decoder verification
7. aborts before reconstruction reporting if any controlled libde265 decode fails

The pipeline accepts `--dec265`, `--width`, `--height`, `--pixel-format`, and `--dec265-threads`. Width, height, and pixel format remain mandatory when dec265 is available because raw YUV output is not self-describing.

The dec265 CLI accepts raw HEVC input, writes decoded YUV with `-o`, and supports a worker-thread argument. citeturn109search327turn109search329turn109search330turn109search331
