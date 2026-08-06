#!/bin/sh
set -eu
VIDEO=$1
OUTPUT=$2
python -m video_forensics.native.host_profile --output "$OUTPUT/host_profile.json"
python -m video_forensics.native.decoder_matrix "$VIDEO" --profile profiles/decoder_matrix/software_single_thread.json --output "$OUTPUT"
python -m video_forensics.native.decoder_matrix "$VIDEO" --profile profiles/decoder_matrix/software_automatic_threads.json --output "$OUTPUT"
