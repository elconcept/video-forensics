# DoD migracji parsera HEVC po Step 61

## Spełnione

- [x] h265nal jest parserem podstawowym dla samodzielnego workflow składni HEVC.
- [x] Build jest przypięty do wskazanej rewizji i zapisuje resolved commit.
- [x] Bootstrap buduje h265nal automatycznie, jeżeli lokalne binarium nie istnieje.
- [x] Adapter zachowuje surowy stdout, stderr, stabilny JSON, źródłowy SHA-256 i polecenie.
- [x] Obsługiwane są obie formy dumpu VPS/SPS/PPS spotykane w dokumentacji CLI.
- [x] Powstaje historia wersji VPS/SPS/PPS i przypisanie aktywnych wersji do obrazów.
- [x] POC i regresja POC są wyprowadzane z danych h265nal.
- [x] Błędy parsera albo rozbieżność legacy blokują automatyczny plan odzysku.
- [x] Istnieje test integracyjny całego adaptera z wykonywalnym procesem CLI.

## Niespełnione

- [ ] Główny etap `hevc_bitstream` nie został jeszcze zastąpiony workflow `video-forensics-hevc-syntax`.
- [ ] Nie wykonano porównania h265nal, legacy i FFmpeg/GStreamer na rzeczywistym strumieniu referencyjnym.
- [ ] Nie potwierdzono lokalnie budowy rzeczywistego upstream h265nal na wszystkich trzech systemach.
- [ ] Parser legacy nie został usunięty.
- [ ] Nie ma pełnego grafu RPS i identyfikacji konkretnej brakującej referencji.
