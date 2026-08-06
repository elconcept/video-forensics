# TOC projektu video-forensics

Mapa plików wygenerowana automatycznie z aktualnego stanu repozytorium.

## Spis sekcji

- [Katalog główny](#katalog-główny)
- [.github](#github)
- [docs](#docs)
- [launchers](#launchers)
- [profiles](#profiles)
- [src](#src)
- [tests](#tests)
- [work](#work)

## Katalog główny

| Plik | Opis |
|---|---|
| `.dockerignore` | Plik pomocniczy projektu. |
| `.gitignore` | Reguły wykluczające lokalne dowody, wyniki, cache i artefakty robocze z repozytorium Git. |
| `cli.patch.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `generate_project_toc.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `git-pipeline.sh` | Skrypt uruchomieniowy lub narzędzie automatyzujące pracę projektu. |
| `gitignore.patch.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `perceptual.patch.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `pyproject.toml` | Konfiguracja pakietu Python, zależności, punkty wejścia CLI oraz narzędzia deweloperskie. |
| `README.md` | Główna instrukcja instalacji i uruchamiania projektu na obsługiwanych hostach. |
| `README.patch.md` | Dokumentacja projektu. |
| `STEP_1.md` | Copy the included files over the repository root, then run: |
| `STEP_10.md` | This stage consumes packet sizes and picture types previously preserved by the GOP stage. It groups frames into fixed windows and reports robust outliers in window packet-size medians. |
| `STEP_11.md` | This stage uses FFprobe to inspect the first audio stream. It preserves packet timestamps, durations, positions, sizes, and stream attributes. |
| `STEP_12.md` | This stage consumes the timeline and audio packet outputs. It compares calculated stream starts and ends and screens for: |
| `STEP_13.md` | This stage exports decoded frames into a separate derivative directory and creates an index with SHA-256 and file size for every output image. |
| `STEP_14.md` | This stage compares an existing analysis output for the questioned recording with an existing analysis output for a reference recording. |
| `STEP_15.md` | This stage creates a Markdown inventory of the analysis run. It records input identity, integrity hashes, stage status, and counts of observation records found in expected output files. |
| `STEP_16.md` | This stage separates the default analysis pipeline from optional operations and adds deterministic dependency expansion. |
| `STEP_17.md` | This step fixes report ordering so that report.md reads a manifest already marked as completed. The final manifest is then written again with the report stage result. |
| `STEP_18.md` | This step strengthens GitHub Actions so every push and pull request performs: |
| `STEP_19.md` | This step adds the first codec-aware layer before pixel-domain interpretation: |
| `STEP_2.md` | This stage runs FFprobe, MediaInfo, and ExifTool independently. It preserves each raw JSON result, records exact commands and version output, and writes a small normalized summary. |
| `STEP_20.md` | The decoder matrix runs directly in Python on Windows. Docker is not used for the hardware-decoder runs. |
| `STEP_21.md` | After copying native run directories from all machines into one common directory, this tool: |
| `STEP_22.md` | Exact framemd5 output may differ because hardware paths can expose different pixel formats, ranges, or conversion behavior. This step adds a second comparison layer. |
| `STEP_23.md` | This step preserves normalized grayscale frames and compares every pair of decoder runs using: |
| `STEP_24.md` | This step adds one PowerShell launcher for both Windows machines. |
| `STEP_25.md` | This step verifies and imports result bundles copied from the Windows machines. |
| `STEP_26.md` | The comparison tools expect one directory containing one child directory per decoder run. Verified imports retain a source-machine directory above each run. |
| `STEP_27.md` | This step replaces the single flattened view with three explicit views: |
| `STEP_28.md` | The README now documents: |
| `STEP_29.md` | This step implements the deployment change from Revision 3: |
| `STEP_3.md` | This stage parses MP4/MOV-family atom headers without modifying or decoding the input. It records offsets, sizes, nesting, top-level order, atom counts, and structural boundary anomalies. |
| `STEP_30.md` | This is the first implementation slice of orphanrecovery. |
| `STEP_31.md` | This step builds controlled test streams from an Annex B HEVC stream and an explicit analyst plan. |
| `STEP_32.md` | This step exports every frame returned by every selected decoder profile into two parallel trees: |
| `STEP_33.md` | This step decodes every controlled stream emitted by orphanstreambuilder into lossless PNG frames. |
| `STEP_34.md` | This step compares controlled orphan-stream decodings produced by two or more decoder implementations. |
| `STEP_35.md` | This step combines the stability output and independent-decoder verification into one structured finding record. |
| `STEP_36.md` | This step adds deterministic audio decoding to signed 16-bit PCM and reports: |
| `STEP_37.md` | This step promotes decoder-matrix execution to one cross-platform entry point. |
| `STEP_38.md` | This step adds a first-class wrapper for the independent dec265 command-line decoder. |
| `STEP_39.md` | This step combines the implemented reconstruction stages into one command: |
| `STEP_4.md` | This stage uses FFprobe to preserve and normalize the first video stream timeline. It writes per-frame timestamps to CSV and reports mechanical timestamp anomalies without interpreting them as evidence of editing. |
| `STEP_40.md` | This step implements the first playback-divergence module. |
| `STEP_41.md` | This step implements staticregionwithmovingframe as a decoded-frame screening module. |
| `STEP_42.md` | This step adds the first osdreader implementation. |
| `STEP_43.md` | This step adds connected-component measurements for pre-cropped burned-in timestamp images. |
| `STEP_44.md` | The README now documents installation, external tools, evidence handling, baseline analysis, host profiling, decoder matrices, Windows/Linux/macOS launchers, complete lossless and email frame export, verified bundle transfer, decoder comparison, audio analysis, orphan recovery, playback-divergence matching, static-region analysis, OSD OCR, glyph screening, status interpretation, validation, and reporting language. |
| `STEP_45.md` | This step extends hevcbitstream with: |
| `STEP_46.md` | This step promotes cross-decoder disagreement from raw comparison tables into structured findings. |
| `STEP_47.md` | This step extends the static-region detector with temporal persistence. |
| `STEP_48.md` | This step adds the missing OSD table required for evidentiary review: |
| `STEP_49.md` | This step removes the need to map OSD images to a generic FFprobe frame table. |
| `STEP_5.md` | This stage independently obtains frame coding information from FFprobe and records: |
| `STEP_50.md` | This step packages the compressed visual-review derivatives for electronic submission without silently discarding the lossless set. |
| `STEP_51.md` | Step 45 deliberately emits only draftrequiresreview. This step closes the enforcement gap. |
| `STEP_52.md` | README was rewritten around direct execution procedures for each target machine. Background discussion was reduced, repeated warnings were consolidated, and the primary workflow is now presented in execution order: installation, per-host runs, transfer, merge, comparison, orphan recovery, submission bundle, and optional visual analysis. |
| `STEP_53.md` | This step adds one launcher per operating system. Every launcher processes all supported files placed directly in work/evidence, creates a UTC session under work/results, and runs baseline analysis, local decoder matrix, complete frame export, audio analysis, email-review packaging, and verified matrix packaging for each file. |
| `STEP_6.md` | This stage decodes the first video stream directly from the source file through FFmpeg. It does not use previously exported PNG, WebP, or TIFF frames. |
| `STEP_7.md` | This stage consumes outputs from the timeline, GOP, and frame-metrics stages. It does not decode the video again. |
| `STEP_8.md` | This stage decodes a deterministic 64 x 36 grayscale stream and calculates: |
| `STEP_9.md` | This stage tests each interior frame against a linear combination of its immediate neighbors. It records the fitted alpha, residual, baseline error, residual ratio, and differences from both neighbors. |

## .github

| Plik | Opis |
|---|---|
| `.github/workflows/ci.yml` | Konfiguracja automatyzacji lub integracji ciągłej. |

## docs

| Plik | Opis |
|---|---|
| `docs/architecture.md` | Dokumentacja projektu. |
| `docs/decoder_dependency.md` | Dokumentacja projektu. |

## launchers

| Plik | Opis |
|---|---|
| `launchers/run_all_linux.sh` | Uruchamia pełny przebieg dla wszystkich plików w work/evidence na natywnym Linuxie. |
| `launchers/run_all_macos.sh` | Uruchamia pełny przebieg dla wszystkich plików w work/evidence na macOS. |
| `launchers/run_all_windows.ps1` | Uruchamia pełny przebieg dla wszystkich plików w work/evidence natywnie w Windows PowerShell. |
| `launchers/run_linux_matrix.sh` | Skrypt uruchomieniowy lub narzędzie automatyzujące pracę projektu. |
| `launchers/run_macos_matrix.sh` | Skrypt uruchomieniowy lub narzędzie automatyzujące pracę projektu. |
| `launchers/run_windows_intel.ps1` | Skrypt uruchomieniowy lub narzędzie automatyzujące pracę projektu. |
| `launchers/run_windows_matrix.ps1` | Skrypt uruchomieniowy lub narzędzie automatyzujące pracę projektu. |
| `launchers/run_windows_nvidia.ps1` | Skrypt uruchomieniowy lub narzędzie automatyzujące pracę projektu. |

## profiles

| Plik | Opis |
|---|---|
| `profiles/decoder_matrix/linux_nvdec.json` | Profil argumentów i wymagań dla konkretnej ścieżki dekodera. |
| `profiles/decoder_matrix/linux_qsv.json` | Profil argumentów i wymagań dla konkretnej ścieżki dekodera. |
| `profiles/decoder_matrix/linux_vaapi.json` | Profil argumentów i wymagań dla konkretnej ścieżki dekodera. |
| `profiles/decoder_matrix/macos_videotoolbox.json` | Profil argumentów i wymagań dla konkretnej ścieżki dekodera. |
| `profiles/decoder_matrix/software_automatic_threads.json` | Profil argumentów i wymagań dla konkretnej ścieżki dekodera. |
| `profiles/decoder_matrix/software_single_thread.json` | Profil argumentów i wymagań dla konkretnej ścieżki dekodera. |
| `profiles/decoder_matrix/windows_intel_d3d11va.json` | Profil argumentów i wymagań dla konkretnej ścieżki dekodera. |
| `profiles/decoder_matrix/windows_intel_qsv.json` | Profil argumentów i wymagań dla konkretnej ścieżki dekodera. |
| `profiles/decoder_matrix/windows_nvidia_cuda.json` | Profil argumentów i wymagań dla konkretnej ścieżki dekodera. |
| `profiles/decoder_matrix/windows_nvidia_d3d11va.json` | Profil argumentów i wymagań dla konkretnej ścieżki dekodera. |

## src

| Plik | Opis |
|---|---|
| `src/video_forensics/__init__.py` | Oznacza katalog jako pakiet Python i może eksportować jego publiczny interfejs. |
| `src/video_forensics/cli.py` | Definiuje główny interfejs wiersza poleceń projektu. |
| `src/video_forensics/init.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `src/video_forensics/manifest.py` | Obsługuje manifesty przebiegów i bezpieczny zapis danych wynikowych. |
| `src/video_forensics/native/__init__.py` | Oznacza katalog jako pakiet Python i może eksportować jego publiczny interfejs. |
| `src/video_forensics/native/audio_samples.py` | Dekoduje audio do PCM i mierzy liczbę oraz udział próbek równych dokładnie zero. |
| `src/video_forensics/native/bundle_decoder_results.py` | Pakuje wyniki dekoderów wraz z manifestem i sumą kontrolną. |
| `src/video_forensics/native/compare_decoder_runs.py` | Porównuje dokładne liczby, kolejność i sumy kontrolne klatek z wielu przebiegów dekoderów. |
| `src/video_forensics/native/compare_normalized_runs.py` | Porównuje znormalizowane wyniki klatkowe między dekoderami. |
| `src/video_forensics/native/compare_perceptual_runs.py` | Porównuje klatki metrykami MAE, RMSE, NCC i udziałem identycznych pikseli. |
| `src/video_forensics/native/decode_orphan_variants.py` | Dekoduje kontrolowane warianty osieroconego ogona do bezstratnych klatek. |
| `src/video_forensics/native/decoder_frame_timestamps.py` | Zapisuje PTS klatek w dokładnej kolejności wyjściowej wybranego profilu dekodera. |
| `src/video_forensics/native/decoder_matrix.py` | Uruchamia pojedynczy profil natywnej macierzy dekoderów i zapisuje jego wyniki. |
| `src/video_forensics/native/decoder_matrix_report.py` | Tworzy hierarchiczne ustalenia z rozbieżności liczby i treści klatek między dekoderami. |
| `src/video_forensics/native/flatten_imported_runs.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `src/video_forensics/native/host_profile.py` | Zapisuje profil systemu, CPU, GPU, sterowników, FFmpeg i dostępnych narzędzi. |
| `src/video_forensics/native/import_decoder_bundles.py` | Weryfikuje i importuje pakiety wyników z innych hostów. |
| `src/video_forensics/native/libde265_run.py` | Uruchamia niezależny dekoder dec265/libde265 i indeksuje surowe klatki YUV. |
| `src/video_forensics/native/normalized_decoder_run.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `src/video_forensics/native/orphan_pipeline.py` | Orkiestruje budowę, dekodowanie, rekonstrukcję i niezależną weryfikację osieroconego ogona. |
| `src/video_forensics/native/orphan_plan_review.py` | Zatwierdza plan rekonstrukcji i wiąże go z SHA-256 konkretnego strumienia Annex B. |
| `src/video_forensics/native/orphan_recovery.py` | Wylicza medianę wariantów, odchylenie i mapę pikseli zależnych od podstawionej referencji. |
| `src/video_forensics/native/orphan_recovery_report.py` | Tworzy strukturalne ustalenie z wyników rekonstrukcji i niezależnej weryfikacji. |
| `src/video_forensics/native/orphan_stream_builder.py` | Składa bajtowo wierne kontrolowane strumienie z parametrów, IDR i osieroconego zakresu VCL. |
| `src/video_forensics/native/osd_glyph_metrics.py` | Mierzy geometrię komponentów glifów nałożonego znacznika czasu. |
| `src/video_forensics/native/osd_reader.py` | Odczytuje nałożony znacznik czasu metodą OCR i wykrywa braki oraz cofnięcia odczytu. |
| `src/video_forensics/native/osd_timeline.py` | Łączy odczyty OSD z PTS klatek pochodzącymi z tego samego przebiegu dekodera. |
| `src/video_forensics/native/perceptual_decoder_run.py` | Eksportuje znormalizowane obrazy do porównań percepcyjnych między dekoderami. |
| `src/video_forensics/native/playback_divergence.py` | Kalibruje kadr nagrania ekranu i porównuje go bez ograniczenia z klatkami standardowymi i odzyskanymi. |
| `src/video_forensics/native/prepare_comparison_views.py` | Tworzy osobne widoki dekoderowe, znormalizowane i percepcyjne z zaimportowanych wyników. |
| `src/video_forensics/native/run_matrix.py` | Wykrywa lokalne możliwości i uruchamia wszystkie dostępne profile dekoderów dla hosta. |
| `src/video_forensics/native/static_region_motion.py` | Wykrywa dokładnie nieruchome regiony przy niezerowej zmianie globalnej klatki. |
| `src/video_forensics/native/static_region_series.py` | Łączy statyczne regiony w serie czasowe i generuje bezstratne wycinki do oględzin. |
| `src/video_forensics/native/submission_bundle.py` | Tworzy zweryfikowany pakiet JPEG do wysyłki z informacją o zachowanych materiałach lossless. |
| `src/video_forensics/native/verify_orphan_decoders.py` | Porównuje rekonstrukcje osieroconego ogona z niezależnych implementacji dekodera. |
| `src/video_forensics/native/visual_frame_export.py` | Eksportuje wszystkie zwrócone klatki równolegle jako PNG lossless i skompresowane JPEG. |
| `src/video_forensics/pipeline.py` | Definiuje kolejność etapów, zależności oraz wykonanie głównego pipeline analitycznego. |
| `src/video_forensics/process.py` | Uruchamia procesy zewnętrzne i zapisuje ich polecenia, wyniki oraz diagnostykę. |
| `src/video_forensics/tools/__init__.py` | Oznacza katalog jako pakiet Python i może eksportować jego publiczny interfejs. |
| `src/video_forensics/tools/audio.py` | Analizuje strumień audio i jego właściwości czasowe. |
| `src/video_forensics/tools/av_sync.py` | Analizuje relację czasową między strumieniami audio i wideo. |
| `src/video_forensics/tools/blending.py` | Wyszukuje kandydatów na liniowe złożenia lub mieszanie klatek. |
| `src/video_forensics/tools/compression.py` | Wykonuje screening zmian charakterystyki kompresji i energii wysokich częstotliwości. |
| `src/video_forensics/tools/container_structure.py` | Analizuje strukturę kontenera MP4/MOV i rozmieszczenie atomów oraz danych. |
| `src/video_forensics/tools/continuity.py` | Analizuje ciągłość obrazu między kolejnymi klatkami. |
| `src/video_forensics/tools/decoder_diagnostics.py` | Zbiera diagnostykę dekodowania, w tym komunikaty o brakujących referencjach. |
| `src/video_forensics/tools/duplicates.py` | Wyszukuje duplikaty klatek i powtarzające się sekwencje. |
| `src/video_forensics/tools/elementary_stream.py` | Wyodrębnia zakodowany strumień elementarny z kontenera. |
| `src/video_forensics/tools/extract_frames.py` | Eksportuje klatki jako materiał pochodny do dalszej analizy. |
| `src/video_forensics/tools/frame_metrics.py` | Wylicza metryki obrazu dla kolejnych zdekodowanych klatek. |
| `src/video_forensics/tools/gop.py` | Analizuje klatki kluczowe, typy obrazów i strukturę GOP. |
| `src/video_forensics/tools/hevc_bitstream.py` | Inwentaryzuje jednostki NAL HEVC i integruje analizę POC oraz nieciągłości sekwencji. |
| `src/video_forensics/tools/hevc_poc.py` | Parsuje niezbędne pola SPS, PPS i nagłówków slice oraz wyprowadza Picture Order Count. |
| `src/video_forensics/tools/integrity.py` | Wylicza sumy kontrolne i identyfikuje plik wejściowy. |
| `src/video_forensics/tools/metadata.py` | Zbiera i porządkuje metadane pliku i strumieni. |
| `src/video_forensics/tools/reference_compare.py` | Porównuje wyniki badanego pliku z osobno przeanalizowanym materiałem referencyjnym. |
| `src/video_forensics/tools/report.py` | Składa wyniki etapów w raport obserwacji bez werdyktu o autentyczności. |
| `src/video_forensics/tools/timeline.py` | Analizuje PTS, DTS, czasy trwania i rytm czasowy próbek wideo. |

## tests

| Plik | Opis |
|---|---|
| `tests/test_audio.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_audio_samples.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_av_sync.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_blending.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_bundle_decoder_results.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_cli.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_compare_decoder_runs.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_compare_normalized_runs.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_compare_perceptual_runs.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_compression.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_container_structure.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_continuity.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_decode_orphan_variants.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_decoder_diagnostics.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_decoder_frame_timestamps.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_decoder_matrix_native.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_decoder_matrix_report.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_duplicates.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_extract_frames.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_flatten_imported_runs.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_frame_metrics.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_gop.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_hevc_bitstream.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_hevc_poc.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_host_profile.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_import_decoder_bundles.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_integrity.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_libde265_run.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_manifest.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_metadata.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_orphan_pipeline.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_orphan_plan_review.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_orphan_recovery.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_orphan_recovery_report.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_orphan_stream_builder.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_osd_glyph_metrics.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_osd_reader.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_osd_timeline.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_package.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_pipeline.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_playback_divergence.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_prepare_comparison_views.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_process.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_reference_compare.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_report.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_report_order.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_run_matrix.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_static_region_motion.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_static_region_series.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_submission_bundle.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_timeline.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_verify_orphan_decoders.py` | Moduł Python wspierający działanie lub testowanie projektu. |
| `tests/test_visual_frame_export.py` | Moduł Python wspierający działanie lub testowanie projektu. |

## work

| Plik | Opis |
|---|---|
| `work/evidence/.gitkeep` | Utrzymuje pusty katalog na lokalne pliki dowodowe; jego pozostała zawartość jest ignorowana przez Git. |
| `work/results/.gitkeep` | Utrzymuje pusty katalog na wyniki analiz; jego pozostała zawartość jest ignorowana przez Git. |

## Podsumowanie

- Łączna liczba opisanych plików: **197**
- Liczba sekcji najwyższego poziomu: **8**
