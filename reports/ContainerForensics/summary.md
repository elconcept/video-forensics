---
source: [https://github.com/ramikhashmel/ContainerForensics]
---
# Raport techniczny 

1. Streszczenie
Przeprowadzono analizę strukturalną pliku wideo w formacie MP4 o nazwie 1796.mp4. Zidentyfikowano osiem cech strukturalnych (dwie o wadze FLAG, sześć o wadze NOTE) wymagających dodatkowej weryfikacji. Struktura pliku wykazuje anomalie w obszarze zakończenia kontenera, gdzie odnotowano błąd parsowania (niezgodność specyfikacji ISO/IEC 14496-12) oraz obecność 625 nadmiarowych bajtów (trailing bytes). Metadane wskazują na prawdopodobne poddanie pliku procesowi rekompresji przy użyciu bibliotek FFmpeg.  

2. Źródła danych
Raport w formacie JSON wygenerowany przez narzędzie ContainerForensics w wersji 0.2.0.  Tabela porównawcza profilów urządzeń (Device-Class Signature Comparison DB v1.1.1) wygenerowana przez ContainerForensics.  Raport z weryfikacji struktury kontenera (Container Structure Triage Report).  Raport krzyżowej walidacji metadanych (Metadata Cross-Validation).  Dokumentacja metodologii analizy ContainerForensics.

3. Ustalenia techniczne
Analizowany kontener posiada rozmiar 2193408 bajtów.  Układ atomów wskazuje na strukturę progresywną, w której atom moov poprzedza mdat (offsety: moov@28, pierwszy mdat@7170).  Plik składa się ze ścieżki wideo vide (Track 1) zakodowanej kodekiem hvc1 oraz ścieżki audio soun (Track 2) zakodowanej kodekiem mp4a.  Atom ftyp deklaruje wiodący brand kontenera jako mp42, z profilami kompatybilnymi: mp42, isom, HKMI.  Tabela offsetów wykorzystuje format 64-bitowy (co64) zarówno dla ścieżki wideo, jak i audio, mimo że plik ma rozmiar poniżej 4 GB.  Nie odnaleziono list edycji (atom elst nie występuje).

4. Artefakty
A6 (Trailing bytes): Niezidentyfikowane dane na końcu pliku o objętości 625 bajtów (rozpoczęcie po offsecie 2192783) znajdujące się poza opisaną strukturą kontenera ISO-BMFF.  P1 (Parser deviation): Wadliwy atom o nagłówku îþ|€ napotkany pod offsetem 2192783, deklarujący wielkość 346733863 bajtów (rozszerzający się do offsetu 348926646, co przekracza faktyczny koniec pliku).

7. Logi
Odnotowano błąd parsowania (Parse Error) wygenerowany przez narzędzie: Box 'îþ|€' declares size 346733863 extending to offset 348926646, beyond its container end 2193408. Treated as truncated. na offsecie 2192783.  8. SystemNIE STWIERDZONO W MATERIALE9. SiećNIE STWIERDZONO W MATERIALE10. PlikiNazwa pliku: 1796.mp4.  Skrót SHA-256: 8560a2d703c1025ba7c5b4deef5e53f89b9ee0c1026cae67b4145e34d137a903.  Wielkość pliku: 2193408 bajtów.

8. Metadane
W atomach mvhd, tkhd[1], tkhd[2], mdhd[0], mdhd[1] zidentyfikowano zerowe czasy utworzenia/modyfikacji (odpowiadające Epoce HFS: 1904-01-01 UTC).  Skala czasu (timescale) dla środowiska zdefiniowana wynosi 1000 dla ścieżki wideo oraz 16000 dla ścieżki audio.  Odnotowano rozbieżność czasu trwania w atomach dla ścieżki audio (Track 2): czas dla tkhd wynosi 12.864s, podczas gdy dla mvhd wynosi 15.669s. Taka sama rozbieżność istnieje pomiędzy mdhd (12.864s) a mvhd (15.669s).

9. Chronologia
1904-01-01 UTC (Epoka Mac HFS): Znaczniki czasu w pliku 1796.mp4 ustawione na wartość zerową (urządzenie nie ustawiło czasu rzeczywistego).  2026-08-06 19:38:46 UTC: Data przeprowadzenia analizy technicznej pliku przez narzędzie ContainerForensics.

10. Korelacje
Obecność tabeli offsetów co64 w pliku o małym rozmiarze koreluje z profilem sygnatury FFmpeg Re-encoded, co logicznie wskazuje na oprogramowanie renderujące (które domyślnie używa 64-bitowych offsetów), a nie natywne nagranie z urządzenia mobilnego czy kamery.  Niezgodność czasów trwania (Track 2 tkhd/mdhd vs mvhd) współwystępująca z profilem środowiska FFmpeg Re-encoded stanowi udokumentowany wzorzec zmontowanego lub dociętego materiału wideo (zgodnie z metodologią Hall, 2015).

11. Czerwone flagi
Anomalia zakończenia struktury: 625 nadmiarowych bajtów po ostatnim zdefiniowanym atomie kontenera. Może to być ukryty nośnik danych lub pozostałość po procesie modyfikacji heksadecymalnej pliku.  Błąd logiczny kontenera: Deklaracja fałszywego atomu w obszarze offsetu 2192783 z nierealistycznym rozmiarem przekraczającym rozmiar nośnika (błąd specyfikacji ISO/IEC 14496-12).  Niezgodność czasowa w nagłówkach Track 2: Wartość tkhd i mdhd rozbieżna względem ogólnej długości mvhd pliku poza granicami tolerancji. 

12. Ograniczenia materiału
Raporty narzędzia pełnią wyłącznie funkcję mechanizmu wstępnego sortowania ("Triage"). Ustalenia techniczne wskazują parametry strukturalne i nie stanowią opinii w przedmiocie pełnej autentyczności samego materiału dowodowego.  Rozpoznanie bazy FFmpeg Re-encoded bazuje na ocenie podobieństwa wzorca (Similarity Score: 4), a nie bezpośredniej identyfikacji unikalnego urządzenia źródłowego. Aktualność bazy profili użytej do analizy zdefiniowana jest na dzień 2026-05-22.

13. Hipotezy wymagające weryfikacji
Plik wideo najprawdopodobniej przeszedł obróbkę poza oryginalnym urządzeniem rejestrującym, najpewniej za sprawą narzędzi wykorzystujących biblioteki FFmpeg (np. kadrowanie, łączenie nagrań, konwersja), na co wskazuje tabela co64, niezgodności w duration Track 2 oraz profil klasy kontenera.Fragment 625-bajtowy na końcu pliku uformował się wskutek nieprawidłowego zapisu pliku wynikowego z programu edycyjnego, ewentualnie intencjonalnie ukryto w nim inny ładunek informacji (tzw. technika concealment). Wymagana jest manualna inspekcja wartości heksadecymalnych zawartości od offsetu 2192783.
