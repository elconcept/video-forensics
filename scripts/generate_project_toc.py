from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}

EXACT_DESCRIPTIONS = {
    ".gitignore": "Reguły wykluczające lokalne dowody, wyniki, cache i artefakty robocze z repozytorium Git.",
    "README.md": "Główna instrukcja instalacji i uruchamiania projektu na obsługiwanych hostach.",
    "pyproject.toml": "Konfiguracja pakietu Python, zależności, punkty wejścia CLI oraz narzędzia deweloperskie.",
    "launchers/run_all_linux.sh": "Uruchamia pełny przebieg dla wszystkich plików w work/evidence na natywnym Linuxie.",
    "launchers/run_all_macos.sh": "Uruchamia pełny przebieg dla wszystkich plików w work/evidence na macOS.",
    "launchers/run_all_windows.ps1": "Uruchamia pełny przebieg dla wszystkich plików w work/evidence natywnie w Windows PowerShell.",
    "work/evidence/.gitkeep": "Utrzymuje pusty katalog na lokalne pliki dowodowe; jego pozostała zawartość jest ignorowana przez Git.",
    "work/results/.gitkeep": "Utrzymuje pusty katalog na wyniki analiz; jego pozostała zawartość jest ignorowana przez Git.",
}

STEM_DESCRIPTIONS = {
    "audio": "Analizuje strumień audio i jego właściwości czasowe.",
    "audio_samples": "Dekoduje audio do PCM i mierzy liczbę oraz udział próbek równych dokładnie zero.",
    "av_sync": "Analizuje relację czasową między strumieniami audio i wideo.",
    "blending": "Wyszukuje kandydatów na liniowe złożenia lub mieszanie klatek.",
    "bundle_decoder_results": "Pakuje wyniki dekoderów wraz z manifestem i sumą kontrolną.",
    "cli": "Definiuje główny interfejs wiersza poleceń projektu.",
    "compare_decoder_runs": "Porównuje dokładne liczby, kolejność i sumy kontrolne klatek z wielu przebiegów dekoderów.",
    "compare_normalized_runs": "Porównuje znormalizowane wyniki klatkowe między dekoderami.",
    "compare_perceptual_runs": "Porównuje klatki metrykami MAE, RMSE, NCC i udziałem identycznych pikseli.",
    "compression": "Wykonuje screening zmian charakterystyki kompresji i energii wysokich częstotliwości.",
    "container_structure": "Analizuje strukturę kontenera MP4/MOV i rozmieszczenie atomów oraz danych.",
    "continuity": "Analizuje ciągłość obrazu między kolejnymi klatkami.",
    "decode_orphan_variants": "Dekoduje kontrolowane warianty osieroconego ogona do bezstratnych klatek.",
    "decoder_diagnostics": "Zbiera diagnostykę dekodowania, w tym komunikaty o brakujących referencjach.",
    "decoder_frame_timestamps": "Zapisuje PTS klatek w dokładnej kolejności wyjściowej wybranego profilu dekodera.",
    "decoder_matrix": "Uruchamia pojedynczy profil natywnej macierzy dekoderów i zapisuje jego wyniki.",
    "decoder_matrix_report": "Tworzy hierarchiczne ustalenia z rozbieżności liczby i treści klatek między dekoderami.",
    "duplicates": "Wyszukuje duplikaty klatek i powtarzające się sekwencje.",
    "elementary_stream": "Wyodrębnia zakodowany strumień elementarny z kontenera.",
    "extract_frames": "Eksportuje klatki jako materiał pochodny do dalszej analizy.",
    "frame_metrics": "Wylicza metryki obrazu dla kolejnych zdekodowanych klatek.",
    "gop": "Analizuje klatki kluczowe, typy obrazów i strukturę GOP.",
    "hevc_bitstream": "Inwentaryzuje jednostki NAL HEVC i integruje analizę POC oraz nieciągłości sekwencji.",
    "hevc_poc": "Parsuje niezbędne pola SPS, PPS i nagłówków slice oraz wyprowadza Picture Order Count.",
    "host_profile": "Zapisuje profil systemu, CPU, GPU, sterowników, FFmpeg i dostępnych narzędzi.",
    "import_decoder_bundles": "Weryfikuje i importuje pakiety wyników z innych hostów.",
    "integrity": "Wylicza sumy kontrolne i identyfikuje plik wejściowy.",
    "libde265_run": "Uruchamia niezależny dekoder dec265/libde265 i indeksuje surowe klatki YUV.",
    "manifest": "Obsługuje manifesty przebiegów i bezpieczny zapis danych wynikowych.",
    "metadata": "Zbiera i porządkuje metadane pliku i strumieni.",
    "orphan_pipeline": "Orkiestruje budowę, dekodowanie, rekonstrukcję i niezależną weryfikację osieroconego ogona.",
    "orphan_plan_review": "Zatwierdza plan rekonstrukcji i wiąże go z SHA-256 konkretnego strumienia Annex B.",
    "orphan_recovery": "Wylicza medianę wariantów, odchylenie i mapę pikseli zależnych od podstawionej referencji.",
    "orphan_recovery_report": "Tworzy strukturalne ustalenie z wyników rekonstrukcji i niezależnej weryfikacji.",
    "orphan_stream_builder": "Składa bajtowo wierne kontrolowane strumienie z parametrów, IDR i osieroconego zakresu VCL.",
    "osd_glyph_metrics": "Mierzy geometrię komponentów glifów nałożonego znacznika czasu.",
    "osd_reader": "Odczytuje nałożony znacznik czasu metodą OCR i wykrywa braki oraz cofnięcia odczytu.",
    "osd_timeline": "Łączy odczyty OSD z PTS klatek pochodzącymi z tego samego przebiegu dekodera.",
    "perceptual_decoder_run": "Eksportuje znormalizowane obrazy do porównań percepcyjnych między dekoderami.",
    "pipeline": "Definiuje kolejność etapów, zależności oraz wykonanie głównego pipeline analitycznego.",
    "playback_divergence": "Kalibruje kadr nagrania ekranu i porównuje go bez ograniczenia z klatkami standardowymi i odzyskanymi.",
    "prepare_comparison_views": "Tworzy osobne widoki dekoderowe, znormalizowane i percepcyjne z zaimportowanych wyników.",
    "process": "Uruchamia procesy zewnętrzne i zapisuje ich polecenia, wyniki oraz diagnostykę.",
    "reference_compare": "Porównuje wyniki badanego pliku z osobno przeanalizowanym materiałem referencyjnym.",
    "report": "Składa wyniki etapów w raport obserwacji bez werdyktu o autentyczności.",
    "run_matrix": "Wykrywa lokalne możliwości i uruchamia wszystkie dostępne profile dekoderów dla hosta.",
    "static_region_motion": "Wykrywa dokładnie nieruchome regiony przy niezerowej zmianie globalnej klatki.",
    "static_region_series": "Łączy statyczne regiony w serie czasowe i generuje bezstratne wycinki do oględzin.",
    "submission_bundle": "Tworzy zweryfikowany pakiet JPEG do wysyłki z informacją o zachowanych materiałach lossless.",
    "timeline": "Analizuje PTS, DTS, czasy trwania i rytm czasowy próbek wideo.",
    "verify_orphan_decoders": "Porównuje rekonstrukcje osieroconego ogona z niezależnych implementacji dekodera.",
    "visual_frame_export": "Eksportuje wszystkie zwrócone klatki równolegle jako PNG lossless i skompresowane JPEG.",
}


def python_description(path: Path) -> str | None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    doc = ast.get_docstring(tree)
    if doc:
        return re.sub(r"\s+", " ", doc).strip().split(". ")[0].rstrip(".") + "."
    return STEM_DESCRIPTIONS.get(path.stem)


def step_description(path: Path) -> str | None:
    if not re.fullmatch(r"STEP_\d+", path.stem):
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return re.sub(r"[`*_]", "", stripped)
    return "Opis zakresu i integracji danego etapu rozwoju projektu."


def describe(path: Path, relative: str) -> str:
    if relative in EXACT_DESCRIPTIONS:
        return EXACT_DESCRIPTIONS[relative]
    if path.name == "__init__.py":
        return "Oznacza katalog jako pakiet Python i może eksportować jego publiczny interfejs."
    if path.suffix == ".py":
        return python_description(path) or "Moduł Python wspierający działanie lub testowanie projektu."
    if path.suffix in {".sh", ".ps1"}:
        return "Skrypt uruchomieniowy lub narzędzie automatyzujące pracę projektu."
    if path.suffix == ".json" and "profiles/decoder_matrix" in relative:
        return "Profil argumentów i wymagań dla konkretnej ścieżki dekodera."
    if path.suffix == ".md":
        return step_description(path) or "Dokumentacja projektu."
    if path.suffix in {".yml", ".yaml"}:
        return "Konfiguracja automatyzacji lub integracji ciągłej."
    if path.suffix == ".toml":
        return "Plik konfiguracji w formacie TOML."
    if path.name == ".gitkeep":
        return "Utrzymuje pusty katalog w repozytorium Git."
    return "Plik pomocniczy projektu."


def files(root: Path) -> list[Path]:
    result: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            result.append(path)
    return sorted(result, key=lambda item: item.relative_to(root).as_posix().lower())


def group_name(relative: Path) -> str:
    return relative.parts[0] if len(relative.parts) > 1 else "Katalog główny"


def build(root: Path) -> str:
    grouped: dict[str, list[Path]] = {}
    for path in files(root):
        relative = path.relative_to(root)
        grouped.setdefault(group_name(relative), []).append(path)

    lines = [
        "# TOC projektu video-forensics",
        "",
        "Mapa plików wygenerowana automatycznie z aktualnego stanu repozytorium.",
        "",
        "## Spis sekcji",
        "",
    ]
    for group in grouped:
        anchor = group.lower().replace(" ", "-").replace(".", "")
        lines.append(f"- [{group}](#{anchor})")

    for group, paths in grouped.items():
        lines.extend(["", f"## {group}", "", "| Plik | Opis |", "|---|---|"])
        for path in paths:
            relative = path.relative_to(root).as_posix()
            description = describe(path, relative).replace("|", "\\|")
            lines.append(f"| `{relative}` | {description} |")

    lines.extend(
        [
            "",
            "## Podsumowanie",
            "",
            f"- Łączna liczba opisanych plików: **{sum(len(value) for value in grouped.values())}**",
            f"- Liczba sekcji najwyższego poziomu: **{len(grouped)}**",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("PROJECT_TOC.md"))
    args = parser.parse_args()
    root = args.root.expanduser().resolve(strict=True)
    output = args.output if args.output.is_absolute() else root / args.output
    output.write_text(build(root), encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(output), "status": "created"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
