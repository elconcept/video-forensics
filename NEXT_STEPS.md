

Plan Step 85–109
Faza I: odzyskanie stabilnej bazy
Step 85: audyt stanu po Step 84
pełny pytest, Ruff, mypy i git diff --check,
lista brakujących plików, importów i entry pointów,
porównanie repozytorium z CHANGE.LOG,
raport bez modyfikowania kodu.
Step 86: test wszystkich importów
automatyczne importowanie każdego modułu src/video_forensics,
wykrywanie self-importów i circular imports,
osobny raport modułów opcjonalnych.
Step 87: audyt entry pointów
utworzyć rrquirements dla pip, dodać tworzenie i aktywacje (omnipotent) dla launcherów
porównanie pyproject.toml z istniejącymi modułami i funkcjami main,
test każdego entry pointu po instalacji editable i wheel,
usunięcie osieroconych poleceń.
Step 88: uporządkowanie executorów i diagnostyki
identyfikacja pozostałych one-time executorów,
przeniesienie użytecznych narzędzi do scripts/dev,
usunięcie jednorazowych fixerów,
zakaz importowania ich przez kod produkcyjny.
Step 89: zabezpieczenie CHANGE.LOG
trwałe pozostawienie make_changelog.py poza pipeline,
test, że git-pipeline.sh nie modyfikuje changelogu,
archiwizacja obecnego SHA-256 CHANGE.LOG,
opis ręcznej polityki aktualizacji.
Faza II: migracja aktywnych konsumentów legacy
Step 90: mapa zależności hevc_poc
symbole importowane przez każdy moduł,
rozróżnienie parsera, modeli danych i prymitywów bitowych,
wskazanie docelowego zamiennika dla każdego symbolu.
Step 91: neutralne modele HEVC
wydzielenie potrzebnych struktur SPS, PPS, slice i POC,
bez logiki parsowania legacy,
modele niezależne od h265nal i FFmpeg.
Step 92: neutralny BitReader
przeniesienie ogólnego czytnika bitowego,
testy bits, ue, se, RBSP,
usunięcie zależności czytnika od hevc_poc.py.
Step 93: migracja short-term RPS
przepięcie modułu i testów na neutralne modele,
dane produkcyjne z normalizacji h265nal,
zachowanie zgodności regresyjnej.
Step 94: migracja long-term RPS
usunięcie importu BitReader z hevc_poc,
wykorzystanie neutralnej warstwy,
testy SPS-selected i slice-defined LTRPS.
Step 95: migracja slice address
przepięcie geometrii CTB i modeli SPS,
zachowanie dokładnej arytmetyki całkowitej,
test wartości granicznych.
Step 96: migracja slice segments
przepięcie modeli SPS/PPS,
zachowanie independent/dependent slice,
test dziedziczenia nagłówka.
Step 97: migracja hevc_bitstream
h265nal jako jedyne produkcyjne źródło składni,
zachowanie inwentarza Annex B i findingów,
brak importów parserów SPS/PPS/POC legacy.
Step 98: migracja orphan_independent_run
pobieranie wymiarów i parametrów z wyniku h265nal,
brak parse_sps z legacy,
jawny błąd przy braku poprawnego SPS.
Step 99: blokada nowych importów legacy
test przeszukujący AST całego src,
zakazane importy hevc_poc, hevc_sps, hevc_pps,
kontrolowana lista wyjątków, początkowo pusta.
Faza III: właściwe usunięcie legacy
Step 100: próba usunięcia w kopii testowej
tymczasowe usunięcie legacy podczas testu,
import całego pakietu,
pełny pytest,
brak zmian destrukcyjnych w repozytorium.
Step 101: finalizer legacy v2
walidacja bramki 1796.mp4,
walidacja braku aktywnych importów,
walidacja wheel i entry pointów,
przerwanie przed usunięciem przy dowolnym błędzie.
Step 102: fizyczne usunięcie legacy
usunięcie hevc_poc.py, hevc_sps.py, hevc_pps.py,
usunięcie eksportera porównawczego,
zachowanie manifestu i wyników regresji jako historii migracji.
Step 103: regresja po usunięciu
pełny pytest,
Ruff i mypy,
build i instalacja wheel,
test wszystkich entry pointów,
ponowny przebieg 1796.mp4.
Faza IV: uszczelnienie pipeline
Step 104: jeden manifest sesji
status każdego modułu i pliku,
UTC start i koniec,
pełne polecenia i wersje narzędzi,
rozróżnienie failed, unavailable i not_applicable.
Step 105: poprawna obsługa wielu plików
błąd jednego pliku nie zatrzymuje pozostałych,
opcjonalny --fail-fast,
osobny status sesji i każdego pliku.
Step 106: blokada współbieżnego zapisu
lock katalogu sesji,
wykrywanie kolizji timestampów,
brak dwóch procesów zapisujących ten sam wynik.
Step 107: smoke test launcherów
Linux i macOS na małym fixture,
kontrola wywoływanych entry pointów,
brak zatrzymania przez niedostępny profil opcjonalny.
Step 108: Windows parity
test składni PowerShell,
prawidłowy zestaw profili Intel i NVIDIA,
automatyczna ścieżka h265nal,
kontrola FFmpeg analogiczna do Linux.
Step 109: zamknięcie migracji i nowy baseline
ponowne wygenerowanie manifestu regresyjnego 1796.mp4,
aktualizacja TODO.md,
zapis końcowego statusu migracji w CHANGE.LOG,
wyznaczenie następnego toru: pełna automatyzacja F1–F19.
Reguła realizacji każdego Stepu

Każdy Step powinien:

przyjść jako tarball,
zawierać idempotentny executor integracyjny,
nie modyfikować CHANGE.LOG,
usuwać executor po integracji,
przejść git-pipeline.sh,
zostać zatwierdzony jako Next Step,
nie rozpoczynać kolejnego Stepu przed pełnym przejściem pipeline.
Co pozostanie po Step 109
automatyzacja F1–F19,
pełny graf zależności RPS,
rozwój rekonstrukcji osieroconego ogona,
rozbudowa macierzy dekoderów,
raport końcowy i dalsze zadania P1–P3.

Wniosek

Nie integrowałbym quevidkit w całości. Warto potraktować projekt jako źródło wybranych algorytmów, testów porównawczych i pomysłów na interfejs, ale nie jako fundament ani nadrzędny silnik analityczny.

Architektura video-forensics jest bardziej rygorystyczna dowodowo: zachowuje wyniki źródłowe, rozdziela właściwości bitstreamu od zachowania dekoderów i zabrania automatycznych werdyktów „autentyczny” lub „zmanipulowany”. TODO.md potwierdza te wymagania.

Co warto przejąć
Element	Ocena	Sposób użyciaAudio spectral continuity	wysoka	Osobny moduł eksperymentalny, bez punktacji autentyczności
Temporal noise consistency	wysoka	Uzupełnienie F5 i analizy zmian źródła
Compression consistency	wysoka	Niezależna kontrola obecnego modułu compression
Scene-cut/GOP correlation	wysoka	Rozszerzenie korelacji GOP i klatek kluczowych
Bitrate bimodality	średnia	Dodatkowa statystyka przesiewowa
Double-compression autocorrelation	średnia	Moduł requires_reference lub screening
Thumbnail mismatch	średnia	Przydatne dla MP4/MOV posiadających miniaturę
Web UI i HTML	średnia	Inspiracja wizualna, nie import całego backendu
FastAPI	niska obecnie	Dopiero po ustabilizowaniu CLI i schematów raportowania
Client-only JavaScript	niska	Osobny produkt, nie obecny priorytet

quevidkit deklaruje m.in. analizę kompresji, scen/GOP, ciągłości spektralnej audio, szumu czasowego, podwójnej kompresji, ELA, struktury bitstreamu, wzorców QP/GOP, miniatury, synchronizacji A/V i bimodalności bitrate.

Czego nie przejmować
1. Werdyktu i agregacji prawdopodobieństwa

quevidkit generuje etykiety authentic, suspicious, tampered i inconclusive oraz łączy wyniki w jedno prawdopodobieństwo.

Na analizowanym 1796.mp4 raport wygenerował kategoryczny wynik TAMPERED, prawdopodobieństwo 83,6% i confidence 90,4%.

Tego modelu nie należy przenosić. Liczby wyglądają precyzyjnie, ale nie są kalibracją dowodową dla konkretnego urządzenia, kodeka i workflow. Są wynikiem wewnętrznego systemu scoringowego.

2. Automatycznej interpretacji korelacji

Raport quevidkit twierdzi, że anomalie w czterech kategoriach znacząco zmniejszają ryzyko false positive.

To zbyt mocny wniosek bez wykazania niezależności detektorów. Wiele sygnałów może pochodzić z jednego procesu, np. transkodowania, remuksowania albo nagrania ekranu.

3. Monolitycznego pipeline

Główny pipeline.py ma ponad 2000 linii. W obecnym projekcie oznaczałoby to pogorszenie audytowalności, testowalności i izolacji etapów.

4. ELA jako finding wysokiej wagi

ELA na klatkach zdekodowanych i ponownie zapisanych jako JPEG jest silnie zależna od dekodera, konwersji kolorów i wybranego poziomu JPEG. Może pozostać wyłącznie screeningiem wizualnym z wyraźną granicą interpretacyjną.

Proponowane miejsce w planie

Step 110: audyt porównawczy quevidkit, bez kopiowania kodu.
Step 111: uruchomienie obu narzędzi na tych samych fixtures.
Step 112: adapter importujący raport quevidkit jako dane zewnętrzne.
Step 113: niezależna implementacja audio spectral continuity.
Step 114: niezależna implementacja temporal noise consistency.
Step 115: scene-cut/GOP correlation.
Step 116: compression-window i bitrate-bimodality screening.
Step 117: porównanie wyników na 1796.mp4.
Step 118: ewentualne wykorzystanie komponentów HTML/UI.

Każdy importowany wynik powinien być oznaczony jako external_screening, bez wpływu na autorytatywne ustalenia HEVC i bez automatycznego werdyktu.

Rekomendacja końcowa: wykorzystać selektywnie około warstwy detektorów i prezentacji, ale zachować własną architekturę, provenance, manifesty, hierarchię dowodową i rygorystyczne granice interpretacyjne. Repozytorium quevidkit
