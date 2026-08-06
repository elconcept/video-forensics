#!/usr/bin/env bash
set -euo pipefail

"$(dirname "$0")/bootstrap_macos.sh"

EVIDENCE_DIR="${1:-work/evidence}"
RESULTS_DIR="${2:-work/results}"
PYTHON="${PYTHON:-python}"

mkdir -p "$EVIDENCE_DIR" "$RESULTS_DIR"
FILES=()
while IFS= read -r -d '' FILE; do FILES+=("$FILE"); done < <(find "$EVIDENCE_DIR" -maxdepth 1 -type f \( \
  -iname '*.mp4' -o -iname '*.mov' -o -iname '*.mkv' -o -iname '*.avi' \
  -o -iname '*.m4v' -o -iname '*.hevc' -o -iname '*.h265' \
\) -print0 | sort -z)

if (( ${#FILES[@]} == 0 )); then
  printf 'ERROR: no supported video files in %s\n' "$EVIDENCE_DIR" >&2
  exit 2
fi

SESSION="$(date -u +%Y%m%dT%H%M%SZ)"
SESSION_DIR="$RESULTS_DIR/$SESSION"
mkdir -p "$SESSION_DIR"
HOST_PROFILE="$SESSION_DIR/host_profile.json"
video-forensics-host-profile --output "$HOST_PROFILE"

PROFILES=(
  profiles/decoder_matrix/software_single_thread.json
  profiles/decoder_matrix/software_automatic_threads.json
  profiles/decoder_matrix/macos_videotoolbox.json
)

for INPUT in "${FILES[@]}"; do
  NAME="$(basename "$INPUT")"
  STEM="${NAME%.*}"
  SAFE_STEM="$(printf '%s' "$STEM" | tr -cs 'A-Za-z0-9._-' '_')"
  OUT="$SESSION_DIR/$SAFE_STEM"
  mkdir -p "$OUT"

  video-forensics analyze "$INPUT" --output "$OUT/baseline"
  video-forensics-run-matrix "$INPUT" --output "$OUT/matrix"

  PROFILE_ARGS=()
  for PROFILE in "${PROFILES[@]}"; do
    [[ -f "$PROFILE" ]] && PROFILE_ARGS+=(--profile "$PROFILE")
  done
  video-forensics-export-visual-frames "$INPUT" \
    --host-profile "$HOST_PROFILE" \
    "${PROFILE_ARGS[@]}" \
    --output "$OUT/visual_frames"

  video-forensics-audio-samples "$INPUT" --output "$OUT/audio_samples"
  video-forensics-submission-bundle "$OUT/visual_frames" \
    --output "$OUT/${SAFE_STEM}_email_review.zip"

  "$PYTHON" -m video_forensics.native.bundle_decoder_results \
    "$OUT/matrix" --output "$OUT/${SAFE_STEM}_matrix.zip"

  video-forensics-result-summary "$OUT"
done

printf 'Completed session: %s\n' "$SESSION_DIR"
