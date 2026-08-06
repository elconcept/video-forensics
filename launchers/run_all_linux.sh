#!/usr/bin/env bash
set -euo pipefail

"$(dirname "$0")/bootstrap_linux.sh"

EVIDENCE_DIR="${1:-work/evidence}"
RESULTS_DIR="${2:-work/results}"
PYTHON="${PYTHON:-python}"

"$PYTHON" scripts/bootstrap_h265nal.py

mkdir -p "$EVIDENCE_DIR" "$RESULTS_DIR"

if [[ ! -d "$EVIDENCE_DIR" ]]; then
  printf 'ERROR: evidence directory not found: %s\n' "$EVIDENCE_DIR" >&2
  exit 2
fi

mapfile -d '' FILES < <(find "$EVIDENCE_DIR" -maxdepth 1 -type f \( \
  -iname '*.mp4' -o -iname '*.mov' -o -iname '*.mkv' -o -iname '*.avi' \
  -o -iname '*.m4v' -o -iname '*.hevc' -o -iname '*.h265' \
\) -print0 | sort -z)

if (( ${#FILES[@]} == 0 )); then
  printf 'ERROR: no supported video files in %s\n' "$EVIDENCE_DIR" >&2
  exit 2
fi

SESSION="$(date -u +%Y%m%dT%H%M%SZ)"
HOST_PROFILE="$RESULTS_DIR/host_profile_${SESSION}.json"
video-forensics-host-profile --output "$HOST_PROFILE"

has_command() {
  command -v "$1" >/dev/null 2>&1
}

json_escape() {
  python -c 'import json,sys; print(json.dumps(sys.stdin.read()))'
}

FFMPEG_HWACCELS="$(ffmpeg -hide_banner -hwaccels 2>&1 || true)"
mapfile -t HWACCELS < <(
  printf '%s\n' "$FFMPEG_HWACCELS" |
    sed -n 's/^[[:space:]]*\([[:alnum:]_][[:alnum:]_]*\)[[:space:]]*$/\1/p' |
    tr '[:upper:]' '[:lower:]' |
    sort -u
)

has_hwaccel() {
  local wanted="$1"
  local item
  for item in "${HWACCELS[@]}"; do
    [[ "$item" == "$wanted" ]] && return 0
  done
  return 1
}

PCI_GPU_TEXT=""
if has_command lspci; then
  PCI_GPU_TEXT="$(lspci -nnk | grep -Eai 'VGA compatible controller|3D controller|Display controller|Kernel driver in use|Kernel modules' || true)"
fi

HAS_INTEL=0
HAS_NVIDIA=0
HAS_AMD=0
printf '%s\n' "$PCI_GPU_TEXT" | grep -Eqi 'Intel' && HAS_INTEL=1 || true
printf '%s\n' "$PCI_GPU_TEXT" | grep -Eqi 'NVIDIA' && HAS_NVIDIA=1 || true
printf '%s\n' "$PCI_GPU_TEXT" | grep -Eqi 'AMD|ATI|Radeon' && HAS_AMD=1 || true

if has_command nvidia-smi && nvidia-smi -L >/dev/null 2>&1; then
  HAS_NVIDIA=1
fi

RENDER_NODES=()
while IFS= read -r node; do
  [[ -n "$node" ]] && RENDER_NODES+=("$node")
done < <(find /dev/dri -maxdepth 1 -type c -name 'renderD*' -print 2>/dev/null | sort || true)

VAAPI_WORKS=0
if (( ${#RENDER_NODES[@]} > 0 )) && has_hwaccel vaapi; then
  if has_command vainfo; then
    for node in "${RENDER_NODES[@]}"; do
      if vainfo --display drm --device "$node" >/dev/null 2>&1; then
        VAAPI_WORKS=1
        break
      fi
    done
  else
    VAAPI_WORKS=1
  fi
fi

QSV_WORKS=0
if (( HAS_INTEL == 1 )) && has_hwaccel qsv && (( ${#RENDER_NODES[@]} > 0 )); then
  QSV_WORKS=1
fi

CUDA_WORKS=0
if (( HAS_NVIDIA == 1 )) && has_hwaccel cuda && has_command nvidia-smi; then
  nvidia-smi -L >/dev/null 2>&1 && CUDA_WORKS=1 || true
fi

PROFILES=(
  profiles/decoder_matrix/software_single_thread.json
  profiles/decoder_matrix/software_automatic_threads.json
)

if (( CUDA_WORKS == 1 )) && [[ -f profiles/decoder_matrix/linux_nvdec.json ]]; then
  PROFILES+=(profiles/decoder_matrix/linux_nvdec.json)
fi
if (( VAAPI_WORKS == 1 )) && [[ -f profiles/decoder_matrix/linux_vaapi.json ]]; then
  PROFILES+=(profiles/decoder_matrix/linux_vaapi.json)
fi
if (( QSV_WORKS == 1 )) && [[ -f profiles/decoder_matrix/linux_qsv.json ]]; then
  PROFILES+=(profiles/decoder_matrix/linux_qsv.json)
fi

{
  printf '{\n'
  printf '  "wsl": %s,\n' "$(grep -Eqi 'microsoft|wsl' /proc/version 2>/dev/null && echo true || echo false)"
  printf '  "vendors": {"intel": %s, "nvidia": %s, "amd": %s},\n' \
    "$([[ $HAS_INTEL -eq 1 ]] && echo true || echo false)" \
    "$([[ $HAS_NVIDIA -eq 1 ]] && echo true || echo false)" \
    "$([[ $HAS_AMD -eq 1 ]] && echo true || echo false)"
  printf '  "render_nodes": ['
  first=1
  for node in "${RENDER_NODES[@]}"; do
    (( first == 0 )) && printf ', '
    printf '"%s"' "$node"
    first=0
  done
  printf '],\n'
  printf '  "ffmpeg_hwaccels": ['
  first=1
  for accel in "${HWACCELS[@]}"; do
    (( first == 0 )) && printf ', '
    printf '"%s"' "$accel"
    first=0
  done
  printf '],\n'
  printf '  "usable": {"vaapi": %s, "qsv": %s, "cuda_nvdec": %s},\n' \
    "$([[ $VAAPI_WORKS -eq 1 ]] && echo true || echo false)" \
    "$([[ $QSV_WORKS -eq 1 ]] && echo true || echo false)" \
    "$([[ $CUDA_WORKS -eq 1 ]] && echo true || echo false)"
  printf '  "selected_profiles": ['
  first=1
  for profile in "${PROFILES[@]}"; do
    (( first == 0 )) && printf ', '
    printf '"%s"' "$profile"
    first=0
  done
  printf ']\n}\n'
} > "$SESSION_DIR/linux_gpu_inventory.json"

printf 'Wykryte backendy GPU: VAAPI=%s QSV=%s CUDA/NVDEC=%s\n' \
  "$VAAPI_WORKS" "$QSV_WORKS" "$CUDA_WORKS"
printf 'Wybrane profile:\n'
printf '  - %s\n' "${PROFILES[@]}"

for INPUT in "${FILES[@]}"; do
  NAME="$(basename "$INPUT")"
  STEM="${NAME%.*}"
  SAFE_STEM="$(printf '%s' "$STEM" | tr -cs 'A-Za-z0-9._-' '_')"
  OUT="$RESULTS_DIR/$SAFE_STEM/$SESSION"
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
  video-forensics-cross-run-compare "$RESULTS_DIR/$SAFE_STEM"
done

printf 'Completed session timestamp: %s\n' "$SESSION"
