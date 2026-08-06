#!/usr/bin/env bash
set -euo pipefail

log() { printf '[bootstrap] %s\n' "$*"; }
has() { command -v "$1" >/dev/null 2>&1; }

REQUIRED_PACKAGES=(python3 python3-venv python3-pip ffmpeg git cmake g++ make)
OPTIONAL_PACKAGES=(mediainfo libimage-exiftool-perl tesseract-ocr gpac libde265-examples pciutils vainfo)

missing_required=()
has python3 || missing_required+=(python3 python3-venv python3-pip)
has ffmpeg || missing_required+=(ffmpeg)
has git || missing_required+=(git)
has cmake || missing_required+=(cmake)
has g++ || missing_required+=(g++)
has make || missing_required+=(make)

missing_optional=()
has mediainfo || missing_optional+=(mediainfo)
has exiftool || missing_optional+=(libimage-exiftool-perl)
has tesseract || missing_optional+=(tesseract-ocr)
has MP4Box || missing_optional+=(gpac)
has lspci || missing_optional+=(pciutils)
has vainfo || missing_optional+=(vainfo)
if ! has dec265 && ! has de265dec; then missing_optional+=(libde265-examples); fi

if (( ${#missing_required[@]} || ${#missing_optional[@]} )); then
  if has apt-get; then
    log "Odświeżanie indeksu APT"
    sudo apt-get update
    if (( ${#missing_required[@]} )); then
      log "Instalowanie wymaganych pakietów: ${missing_required[*]}"
      sudo apt-get install -y --no-install-recommends "${missing_required[@]}"
    fi
    for package in "${missing_optional[@]}"; do
      log "Próba instalacji opcjonalnego pakietu: $package"
      sudo apt-get install -y --no-install-recommends "$package" || \
        log "Opcjonalny pakiet niedostępny przez APT: $package"
    done
  else
    log "Brak apt-get. Automatyczna instalacja systemowa jest niedostępna."
  fi
fi

if ! has ffmpeg && has snap; then
  log "Próba awaryjnej instalacji FFmpeg przez Snap"
  sudo snap install ffmpeg || true
fi

if ! has python3; then
  log "ERROR: brak python3 po bootstrapie"
  exit 2
fi
if ! has ffmpeg || ! has ffprobe; then
  log "ERROR: brak ffmpeg lub ffprobe po bootstrapie"
  exit 2
fi

if [[ ! -d .venv ]]; then
  log "Tworzenie .venv"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'

log "Bootstrap Linux/WSL zakończony"
