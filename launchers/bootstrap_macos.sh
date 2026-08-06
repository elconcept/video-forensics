#!/usr/bin/env bash
set -euo pipefail

log() { printf '[bootstrap] %s\n' "$*"; }
has() { command -v "$1" >/dev/null 2>&1; }

if ! has brew; then
  log "Instalowanie Homebrew"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
fi

required_formulae=(python@3.12 ffmpeg)
optional_formulae=(mediainfo exiftool tesseract gpac libde265)

for formula in "${required_formulae[@]}"; do
  if ! brew list --formula "$formula" >/dev/null 2>&1; then
    log "Instalowanie wymaganego pakietu Homebrew: $formula"
    brew install "$formula"
  fi
done

for formula in "${optional_formulae[@]}"; do
  if ! brew list --formula "$formula" >/dev/null 2>&1; then
    log "Próba instalacji opcjonalnego pakietu Homebrew: $formula"
    brew install "$formula" || log "Opcjonalny pakiet niedostępny: $formula"
  fi
done

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

log "Bootstrap macOS zakończony"
