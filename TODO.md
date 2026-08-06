# TODO projektu `video-forensics`

Lista obejmuje elementy, które pozostają do implementacji, integracji albo walidacji po Step 53. Nie obejmuje funkcji już ukończonych, chyba że wymagają domknięcia.

## P0 — integralność i poprawność pipeline

- [ ] Przeprowadzić pełny audyt aktualnego repozytorium po integracji wszystkich Stepów.
- [ ] Usunąć pozostałe self-importy, circular imports i artefakty błędnych nakładek.
- [ ] Sprawdzić zgodność `pyproject.toml` ze wszystkimi rzeczywiście istniejącymi punktami wejścia.
- [ ] Dodać test importu każdego modułu i każdego entry pointu.
- [ ] Dodać test uruchomienia `--help` dla wszystkich komend CLI.
- [ ] Zweryfikować, że launchery wywołują wyłącznie istniejące komendy, profile i moduły.
- [ ] Sprawdzić, czy każdy moduł zapisuje wynik poza katalogiem dowodowym.
- [ ] Wymusić sprawdzenie, że katalog wynikowy nie znajduje się wewnątrz `work/evidence`.
- [ ] Zapisywać UTC start i koniec każdego modułu oraz całej sesji.
- [ ] Ujednolicić statusy: `completed`, `failed`, `decoder_error`, `unavailable`, `not_applicable`, `pending`.
- [ ] Dodać końcowy manifest sesji obejmujący status wszystkich etapów dla każdego pliku.
- [ ] Dodać możliwość wznowienia przerwanej sesji bez nadpisywania ukończonych wyników.
- [ ] Dodać tryb `--fail-fast` oraz domyślny tryb kontynuowania analizy pozostałych plików po błędzie jednego pliku.

## P0 — test referencyjny `1796.mp4`

- [ ] Dodać lokalny test akceptacyjny sprawdzający nazwę, rozmiar i SHA-256 pliku referencyjnego.
- [ ] Zautomatyzować uruchomienie testów F1–F19 na pliku referencyjnym.
- [ ] Zapisywać dla każdego testu: `passed`, `failed`, `unavailable` albo `requires_reference`.
- [ ] Zweryfikować F1: 201031 z 205824 próbek audio równych dokładnie zero.
- [ ] Zweryfikować F2: audio krótsze od wideo o 2,805 s.
- [ ] Zweryfikować F3: klatki kluczowe 1, 52, 112 i 142.
- [ ] Zweryfikować F4: skok metryk na klatce 142.
- [ ] Zweryfikować F5: zmianę mediany energii wysokich częstotliwości.
- [ ] Zweryfikować F6: regresję POC 50 → 1 bez IRAP i 44 diagnostyki brakujących referencji.
- [ ] Zweryfikować F7: 625 bajtów za `mdat`, ich entropię i brak start code.
- [ ] Zweryfikować F8–F12 w strukturze kontenera i metadanych.
- [ ] Zweryfikować F13–F15 w strumieniu HEVC.
- [ ] Zweryfikować F16: zmianę rytmu `stts` od klatki 141.
- [ ] Zweryfikować F17: rozbieżne liczby i treść klatek między ścieżkami dekodowania.
- [ ] Zweryfikować F18: udział pikseli zdeterminowanych oraz niezależną zgodność dekoderów.
- [ ] Zweryfikować F19: dopasowanie odzyskanych klatek do nagrania ekranu po kalibracji.
- [ ] Dodać raport regresji porównujący bieżące wyniki z zatwierdzonym wzorcem referencyjnym.

## P0 — HEVC, POC i RPS

- [x] Dokończyć parser SPS zamiast kończyć go po polach potrzebnych do `log2_max_poc_lsb`.
- [x] Dokończyć parser PPS.
- [x] Obsłużyć pełny nagłówek pierwszego i zależnego segmentu slice.
- [ ] Poprawnie obsłużyć `slice_segment_address`.
- [ ] Parsować short-term reference picture sets z SPS i slice header.
- [ ] Parsować long-term reference pictures.
- [ ] Wyprowadzać pełny graf zależności RPS dla każdego obrazu.
- [ ] Identyfikować konkretną brakującą referencję dla każdego slice’a.
- [ ] Obsłużyć zasady aktualizacji poprzedniego POC dla RASL, RADL i sub-layer non-reference.
- [ ] Obsłużyć `NoRaslOutputFlag`, IDR, BLA i CRA.
- [ ] Wykrywać regresję POC bez IRAP jako osobne ustalenie wysokiej wagi.
- [ ] Grupować kolejne zależne slice’y w jeden zakres osieroconej sekwencji.
- [ ] Generować plan rekonstrukcji z właściwym zestawem VPS/SPS/PPS obowiązującym przy każdym IDR.
- [ ] Odrzucać automatyczny draft planu, jeżeli parser zgłosił błąd w SPS, PPS lub nagłówku slice dotyczącym zakresu.
- [ ] Dodać eksport grafu: obraz → wymagane referencje → status obecności.
- [ ] Dodać testy jednostkowe na rzeczywistych i syntetycznych strumieniach HEVC.

## P0 — rekonstrukcja osieroconego ogona

- [ ] Zintegrować `dec265` bezpośrednio z `orphan_pipeline` dla wszystkich kontrolowanych wariantów.
- [ ] Konwertować wynik YUV z libde265 do bezstratnych PNG bez zmiany kolejności klatek.
- [ ] Dodać manifest zgodny z `verify_orphan_decoders` dla libde265.
- [ ] Dodać uruchomienie niezależnego dekodera jednym poleceniem, bez ręcznego przygotowania drzewa wyników.
- [ ] Weryfikować identyczny SHA-256 każdego kontrolowanego strumienia przed porównaniem dekoderów.
- [ ] Weryfikować jednakową geometrię, przestrzeń kolorów i zakres wartości.
- [ ] Zapisywać per-pixel medianę, odchylenie standardowe i maskę determinacji także w formacie numerycznym.
- [ ] Zapisywać udział pikseli zdeterminowanych osobno dla każdego kanału i dla całego piksela.
- [ ] Dodać konfigurowalne kryterium determinacji z jawnym uzasadnieniem progu.
- [ ] Dodać kontrolę wrażliwości wyniku na wybrany próg σ.
- [ ] Dodać test, że raport nie jest emitowany bez niezależnego dekodera.
- [ ] Dodać test, że builder nie przyjmuje draftu ani planu powiązanego z innym SHA-256.
- [ ] Dodać pełną ścieżkę: draft → zatwierdzenie → budowa → decode → recovery → verify → report.

## P0 — macierz dekoderów

- [ ] Zweryfikować rzeczywisty schemat istniejącego `decoder_matrix.py` przed dalszą integracją.
- [ ] Dodać libde265 jako pełnoprawną ścieżkę macierzy.
- [ ] Dodać natywny runner AVFoundation dla macOS.
- [ ] Dodać identyfikację faktycznie wybranego adaptera GPU.
- [ ] Dodać jawne rozróżnienie D3D11VA Intel i D3D11VA NVIDIA.
- [ ] Sprawdzać obsługę HEVC przez konkretny adapter przed uruchomieniem profilu.
- [ ] Rejestrować sterownik i identyfikator urządzenia przy każdym hardware run.
- [ ] Rozróżnić „profil uruchomiony” od „sprzętowy dekoder faktycznie użyty”.
- [ ] Dodać wykrywanie software fallback.
- [ ] Dodać test, że single-thread i automatic-thread są oddzielnymi obowiązkowymi przebiegami.
- [ ] Dodać raport grupujący dekodery według liczby zwróconych klatek.
- [ ] Dodać pojedyncze wyróżnione finding dla rozbieżności liczby klatek.
- [ ] Klasyfikować rozbieżność tylko jednego backendu jako `decoder_specific`.
- [ ] Klasyfikować wspólne miejsce rozbieżności wielu niezależnych implementacji jako wymagające analizy bitstreamu.
- [ ] Powiązać pierwszą rozbieżną klatkę z NAL, POC, GOP i aktywnym zestawem parametrów.

## P1 — launchery i automatyzacja wielu plików

- [ ] Zintegrować Step 53 z głównym README zamiast przechowywać osobny `README.patch.md`.
- [ ] Dodać test składni PowerShell dla `run_all_windows.ps1` na Windows CI.
- [ ] Dodać testy smoke launcherów Linux i macOS na pliku syntetycznym.
- [ ] Upewnić się, że brak jednego opcjonalnego profilu nie zatrzymuje przetwarzania pliku.
- [ ] Upewnić się, że błąd jednego pliku nie zatrzymuje pozostałych, chyba że użyto `--fail-fast`.
- [ ] Dodać osobny status sesji i status każdego pliku.
- [ ] Dodać bezpieczne nazwy katalogów także dla kolizji nazw plików o różnych rozszerzeniach.
- [ ] Uwzględnić SHA-256 w nazwie lub identyfikatorze wyniku pliku.
- [ ] Dodać blokadę przed równoczesnym zapisem dwóch procesów do tej samej sesji.
- [ ] Sprawdzić, czy `bundle_decoder_results` przyjmuje dokładnie strukturę generowaną przez `run_matrix`.
- [ ] Sprawdzić, czy pakiet email nie jest tworzony, gdy eksport klatek dla wszystkich profili zakończył się niepowodzeniem.
- [ ] Dodać natywny launcher Windows przeznaczony dla X1 Carbon: software, QSV i Intel D3D11VA.
- [ ] Dodać natywny launcher Windows dla H110: software, Intel D3D11VA, NVIDIA D3D11VA i NVDEC.
- [ ] Nie traktować WSL na X1 jako oddzielnego hosta macierzy dowodowej.

## P1 — eksport klatek i materiał do oględzin

- [ ] Zweryfikować numerację klatek między PNG, JPEG, PTS i manifestem dekodera.
- [ ] Dodać PTS do `index.csv` eksportu klatek.
- [ ] Dodać identyfikator profilu i SHA-256 źródła do każdego indeksu.
- [ ] Dodać osobny manifest dla każdego katalogu klatek.
- [ ] Zapisywać parametry konwersji koloru i pixel format.
- [ ] Dodać opcję eksportu bez konwersji kolorów tam, gdzie format na to pozwala.
- [ ] Dodać generowanie arkuszy kontaktowych do szybkiej analizy wizualnej.
- [ ] Dodać opcjonalne wycinki wokół wszystkich wykrytych anomalii.
- [ ] Dodać pakiet lossless do przekazania na żądanie wraz z zewnętrznym SHA-256.
- [ ] Dodać kontrolę maksymalnego rozmiaru paczki email i automatyczny podział na części.
- [ ] Dodać manifest części archiwum i kolejność ich scalania.

## P1 — playback divergence

- [ ] Zapisywać SHA-256 klatki kontrolnej i wszystkich kandydatów.
- [ ] Dodać transformację perspektywiczną, nie tylko prostokątny crop i skalę.
- [ ] Dodać korektę obrotu i niewielkiego przechylenia ekranu.
- [ ] Zapisywać pełną przestrzeń przeszukanych parametrów kalibracji.
- [ ] Dodać próg jakości kalibracji kontrolnej.
- [ ] Odrzucać analizę, gdy kalibracja kontrolna jest niewystarczająca.
- [ ] Dodać porównanie standardowych i odzyskanych klatek jako osobnych grup.
- [ ] Dodać model blend/tear.
- [ ] Dla każdego dopasowania blend wykonać obowiązkowe przeszukanie nieograniczone.
- [ ] Oznaczać wynik jako przeuczony, jeżeli pełne przeszukanie znajduje lepszą parę poza zakładanym zakresem.
- [ ] Dodać raport kontroli pasma NCC na klatkach o znanym dopasowaniu.
- [ ] Generować wizualne nakładki różnic dla najlepszego i drugiego dopasowania.

## P1 — statyczne regiony

- [ ] Połączyć `static_region_motion` i `static_region_series` w jeden etap pipeline.
- [ ] Dodać PTS do każdej pary i serii.
- [ ] Dodać rzeczywistą estymację ruchu globalnego, nie tylko pełnoklatkowy MAE.
- [ ] Kompensować ruch globalny przed badaniem identyczności regionu.
- [ ] Rozróżniać nieruchomy overlay od regionu poruszającego się razem z obiektem.
- [ ] Weryfikować region równolegle na wynikach wielu dekoderów.
- [ ] Oznaczać region jako bitstream-consistent tylko przy zgodności niezależnych dekoderów.
- [ ] Dodać dedykowany test referencyjny dla klatek 173–182.
- [ ] Generować wycinki przed, w trakcie i po wykrytej serii.

## P1 — OSD i timestamp

- [ ] Zintegrować zapis cropów OSD używanych przez OCR.
- [ ] Dodać SHA-256 cropu do każdego odczytu.
- [ ] Dodać confidence OCR per znak i per napis.
- [ ] Dodać warianty preprocessingu i wybór najlepszego wyniku bez ukrywania alternatyw.
- [ ] Dodać ręczną korektę odczytu z zachowaniem wartości OCR i audytu zmiany.
- [ ] Połączyć `osd_reader`, `osd_timeline` i `osd_glyph_metrics` w jeden workflow.
- [ ] Zapisywać PTS bezpośrednio podczas eksportu klatek zamiast wykonywać drugi decode tylko dla `showinfo`.
- [ ] Dodać kontrolę, że profil i SHA-256 timestampów są zgodne z profilem i SHA-256 obrazów.
- [ ] Dodać segmentację pojedynczych glifów na podstawie odczytanego tekstu.
- [ ] Porównywać te same cyfry między pozycjami i klatkami.
- [ ] Dodać analizę linii bazowej cyfr roku w obrębie jednego napisu.
- [ ] Dodać test automatyczny na jednosekundowe cofnięcie odczytu.
- [ ] Dodać wizualny raport OCR z zaznaczonym tekstem i glifami.

## P1 — audio

- [ ] Ustalić i konsekwentnie opisać, czy licznik dotyczy próbek skalarnych czy ramek wielokanałowych.
- [ ] Zapisywać SHA-256 surowego PCM użytego do analizy.
- [ ] Dodać analizę ciągłych zakresów dokładnych zer.
- [ ] Dodać początek, koniec i długość każdego zakresu ciszy cyfrowej.
- [ ] Dodać histogram amplitud i udział wartości bliskich zeru osobno od dokładnego zera.
- [ ] Dodać analizę nieciągłości waveformu i fazy na granicach segmentów.
- [ ] Dodać packet-level korelację z timeline kontenera.
- [ ] Dodać test referencyjny F1 i F2.
- [ ] Nie emitować „niskiej przepływności” jako samodzielnego finding.

## P1 — kontener i metadane

- [ ] Dodać pełną walidację sumy `stsz` względem payloadu `mdat`.
- [ ] Dodać wykrywanie nieindeksowanych zakresów `mdat`.
- [ ] Dodać analizę danych za końcem `mdat` wraz z entropią i próbami interpretacji.
- [ ] Rozróżniać dane za `mdat` od danych za końcem pliku.
- [ ] Dodać wykrywanie start code w danych końcowych.
- [ ] Dodać kontrolę atomów `mvhd`, `tkhd`, `mdhd`, `hdlr`, `stco` i `co64`.
- [ ] Oznaczać F8–F11 jako `requires_reference: true`.
- [ ] Dodać moduł porównujący kontener z materiałem referencyjnym urządzenia.
- [ ] Dodać bazę profili referencyjnych urządzeń bez automatycznego wnioskowania o źródle.

## P1 — raport końcowy

- [ ] Ujednolicić schemat findingów we wszystkich modułach.
- [ ] Wymagać pól: `id`, `severity`, `description`, `evidence_refs`, `requires_reference`, `host_profile`.
- [ ] Dodać pole rozróżniające fakt bitstreamowy, wynik dekodera i wynik obrazu pochodnego.
- [ ] Dodać pole `source_sha256` do każdego finding.
- [ ] Dodać agregację tego samego finding z wielu hostów.
- [ ] Dodać hierarchię dowodową: bitstream, kontener, dekoder, obraz pochodny, nagranie ekranu.
- [ ] Oddzielić diagnostykę narzędzia od właściwości badanego pliku.
- [ ] Nie raportować komunikatów muxera wyjściowego jako diagnostyki dowodu.
- [ ] Wyróżniać rozbieżność liczby klatek jako osobne ustalenie wysokiej wagi.
- [ ] Dodać korelację findings z dokładnym NAL, POC, PTS, GOP i klatką.
- [ ] Dodać skrócony raport dla kancelarii/prokuratury i pełny raport techniczny.
- [ ] Dodać spis załączników i sumy SHA-256 wszystkich materiałów raportowych.
- [ ] Zagwarantować brak automatycznych sformułowań „autentyczny” i „zmanipulowany”.

## P2 — dokumentacja i utrzymanie

- [ ] Wygenerować `PROJECT_TOC.md` z aktualnego repozytorium.
- [ ] Dodać generator TOC do repozytorium, np. `scripts/generate_project_toc.py`.
- [ ] Aktualizować TOC automatycznie w CI i wykrywać nieaktualną wersję.
- [ ] Zintegrować instrukcję Step 53 z README.
- [ ] Usunąć albo zarchiwizować przestarzałe pliki `STEP_N.md` po utrwaleniu historii w Git.
- [ ] Dodać `CHANGELOG.md`.
- [ ] Dodać dokument opisujący schematy JSON i CSV.
- [ ] Dodać dokument opisujący interpretację każdego severity.
- [ ] Dodać instrukcję instalacji narzędzi zewnętrznych dla Ubuntu, Windows i macOS.
- [ ] Dodać instrukcję pozyskania zgodnego builda FFmpeg dla każdej platformy.
- [ ] Dodać licencję przed publiczną dystrybucją.

## P2 — CI i jakość kodu

- [ ] Dodać CI dla Linux, Windows i macOS.
- [ ] Uruchamiać testy na Pythonie 3.12.
- [ ] Dodać test budowy pakietu wheel i instalacji z wheel.
- [ ] Dodać testy entry pointów po instalacji pakietu.
- [ ] Dodać statyczne sprawdzanie typów.
- [ ] Dodać testy schematów JSON.
- [ ] Dodać testy bezpieczeństwa ścieżek ZIP.
- [ ] Dodać testy nazw plików ze spacjami i znakami Unicode.
- [ ] Dodać testy braku narzędzi opcjonalnych.
- [ ] Dodać testy timeoutów i częściowych wyników.
- [ ] Dodać testy na uszkodzonych i niepełnych plikach wejściowych.
- [ ] Dodać małe, legalnie dystrybuowalne fixtures HEVC do testów jednostkowych.

## P2 — wydajność

- [ ] Ograniczyć wielokrotne dekodowanie tego samego profilu przez współdzielenie bezstratnego wyniku i PTS.
- [ ] Dodać cache powiązany z SHA-256 wejścia, profilem hosta i pełnym poleceniem.
- [ ] Dodać przetwarzanie strumieniowe mediany i σ dla dużej liczby wariantów.
- [ ] Ograniczyć pamięć podczas porównań pełnych klatek 4K.
- [ ] Dodać kontrolę wolnego miejsca przed eksportem wszystkich klatek.
- [ ] Szacować rozmiar wyników przed rozpoczęciem analizy.
- [ ] Dodać opcjonalną równoległość na poziomie plików bez współdzielenia katalogów wynikowych.

## P3 — dalsze rozszerzenia badawcze

- [ ] Dodać analizę PRNU, jeśli dostępny będzie odpowiedni materiał referencyjny.
- [ ] Dodać analizę ENF dla materiałów z odpowiednim sygnałem audio.
- [ ] Dodać analizę motion vectors z bitstreamu.
- [ ] Dodać analizę QP per CTU i map zmian parametrów kompresji.
- [ ] Dodać analizę deblockingu i SAO.
- [ ] Dodać korelację zmian `stts`, GOP, rozdzielczości, sceny i zestawów parametrów.
- [ ] Dodać bibliotekę kontrolowanych eksperymentów z usuwaniem IDR i porównaniem polityk concealment.
- [ ] Dodać test hipotezy VLC/D3D11VA dotyczącej zawartości bufora referencyjnego.
- [ ] Dodać workflow porównania z referencyjnym nagraniem EZVIZ CS-DP2C, gdy materiał będzie dostępny.

## Definicja ukończenia funkcji

Każda nowa funkcja jest ukończona dopiero, gdy:

- [ ] ma test jednostkowy,
- [ ] ma co najmniej jeden test integracyjny,
- [ ] zapisuje pełne parametry i wersje narzędzi,
- [ ] wiąże wynik z SHA-256 wejścia,
- [ ] nie zapisuje do katalogu dowodowego,
- [ ] zachowuje pełne logi,
- [ ] degraduje się jawnie przy braku opcjonalnego narzędzia,
- [ ] rozróżnia właściwość bitstreamu od wyniku dekodera,
- [ ] posiada granicę interpretacyjną,
- [ ] nie wydaje werdyktu o autentyczności.
