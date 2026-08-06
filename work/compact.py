import os
import re


def update_changelog_and_cleanup():
    # Krok 1: Szukamy nowych plików STEP (np. STEP_13.md, STEP_14.md)
    pattern = re.compile(r'^STEP_(\d+)\.md$')
    step_files = []

    for filename in os.listdir('.'):
        match = pattern.match(filename)
        if match:
            # Zapisujemy numer kroku i nazwę pliku
            step_number = int(match.group(1))
            step_files.append((step_number, filename))

    # Jeśli nie ma żadnych nowych plików, informujemy o tym i kończymy działanie
    if not step_files:
        print("Brak nowych plików STEP do dodania.")
        return

    # Sortujemy pliki malejąco, aby najnowsze wpisy były na samej górze
    step_files.sort(key=lambda x: x[0], reverse=True)

    # Krok 2: Zabezpieczamy to, co już znajduje się w pliku CHANGE.LOG
    old_content = ""
    if os.path.exists('CHANGE.LOG'):
        with open('CHANGE.LOG', 'r', encoding='utf-8') as log_file:
            old_content = log_file.read()

    # Krok 3: Zapisujemy zaktualizowaną zawartość i usuwamy przetworzone pliki
    with open('CHANGE.LOG', 'w', encoding='utf-8') as log_file:
        
        # A) Zapisujemy zawartość NOWYCH plików STEP
        for step_number, filename in step_files:
            # Tworzymy nagłówek dla łatwiejszej identyfikacji
            log_file.write(f"### --- Pochodzi z pliku: {filename} ---\n\n")
            
            # Odczytujemy zawartość pliku STEP i zapisujemy do CHANGE.LOG
            with open(filename, 'r', encoding='utf-8') as step_file:
                log_file.write(step_file.read())
                log_file.write("\n\n\n")
            
            # NOWOŚĆ: Usuwamy plik z dysku po jego pomyślnym skopiowaniu
            # Funkcja os.remove() trwale kasuje plik o podanej nazwie
            os.remove(filename)
        
        # B) Doklejamy starą zawartość na samym dole pliku
        if old_content:
            log_file.write(old_content)

    # Wyświetlamy podsumowanie operacji
    print(f"Sukces! Zaktualizowano CHANGE.LOG i trwale usunięto {len(step_files)} przetworzonych plików STEP.")

# Punkt wejścia - tutaj skrypt rozpoczyna swoje działanie
if __name__ == '__main__':
    update_changelog_and_cleanup()