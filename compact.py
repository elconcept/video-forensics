import os
import re


def generate_changelog():
    # Krok 1: Definiujemy wzorzec nazwy pliku (szukamy plików STEP_<liczba>.md)
    pattern = re.compile(r'^STEP_(\d+)\.md$')
    step_files = []

    # Krok 2: Przeglądamy wszystkie pliki w obecnym folderze (oznaczonym jako '.')
    for filename in os.listdir('.'):
        match = pattern.match(filename)
        if match:
            # Wyciągamy numer z nazwy pliku (np. z "STEP_12.md" wyciągnie liczbę 12)
            step_number = int(match.group(1))
            # Zapisujemy parę: (numer_kroku, nazwa_pliku) do naszej listy
            step_files.append((step_number, filename))

    # Zabezpieczenie, jeśli w folderze nie ma odpowiednich plików
    if not step_files:
        print("Nie znaleziono żadnych plików STEP_<n>.md w tym katalogu.")
        return

    # Krok 3: Sortujemy listę na podstawie numeru kroku, malejąco (najnowsze na górze)
    step_files.sort(key=lambda x: x[0], reverse=True)

    # Krok 4: Tworzymy i otwieramy plik CHANGE.LOG w trybie pisania ('w')
    with open('CHANGE.LOG', 'w', encoding='utf-8') as log_file:
        for step_number, filename in step_files:
            
            # Tworzymy nagłówek dla każdego kroku
            log_file.write(f"### --- Pochodzi z pliku: {filename} ---\n\n")
            
            # Odczytujemy zawartość pliku STEP
            with open(filename, 'r', encoding='utf-8') as step_file:
                content = step_file.read()
                log_file.write(content)
                log_file.write("\n\n\n") # Dodajemy trochę pustego miejsca dla czytelności

    # Wyświetlamy radosny komunikat na koniec!
    print(f"Sukces! Plik CHANGE.LOG został pomyślnie wygenerowany z {len(step_files)} plików.")

# Ten fragment upewnia się, że skrypt uruchomi się poprawnie
if __name__ == '__main__':
    generate_changelog()