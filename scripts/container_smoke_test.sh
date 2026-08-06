#!/bin/sh
set -eu

IMAGE=${1:-video-forensics:smoke}
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT INT TERM

chmod 0755 "$WORK_DIR"
 install -d -m 0777 "$WORK_DIR/evidence" "$WORK_DIR/results"

docker build --tag "$IMAGE" .

docker run --rm --user "$(id -u):$(id -g)" \
  --entrypoint /usr/bin/ffmpeg \
  -v "$WORK_DIR/evidence:/evidence:rw" \
  "$IMAGE" \
  -nostdin -v error \
  -f lavfi -i testsrc2=size=320x180:rate=25 \
  -f lavfi -i sine=frequency=1000:sample_rate=48000 \
  -t 2 \
  -c:v libx264 -pix_fmt yuv420p \
  -c:a aac \
  /evidence/smoke.mp4

docker run --rm --user "$(id -u):$(id -g)" \
  --network none \
  --read-only \
  --tmpfs /tmp:size=512m \
  --security-opt no-new-privileges:true \
  -v "$WORK_DIR/evidence:/evidence:ro" \
  -v "$WORK_DIR/results:/results:rw" \
  "$IMAGE" \
  analyze /evidence/smoke.mp4 \
  --output /results/smoke

test -f "$WORK_DIR/results/smoke/manifest.json"
test -f "$WORK_DIR/results/smoke/report.md"
test -f "$WORK_DIR/results/smoke/integrity/hashes.json"
test -f "$WORK_DIR/results/smoke/metadata/raw/ffprobe.json"
test -f "$WORK_DIR/results/smoke/container/structure.json"
test -f "$WORK_DIR/results/smoke/timeline/frames.csv"
test -f "$WORK_DIR/results/smoke/gop/gops.csv"
test -f "$WORK_DIR/results/smoke/frame_metrics/metrics.csv"
test -f "$WORK_DIR/results/smoke/audio/packets.csv"
test -f "$WORK_DIR/results/smoke/av_sync/av_sync.json"

python3 - "$WORK_DIR/results/smoke/manifest.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    manifest = json.load(handle)

assert manifest["run"]["status"] == "completed"
assert "report" in manifest["stages"]
PY

printf '%s\n' "Container smoke test passed"
