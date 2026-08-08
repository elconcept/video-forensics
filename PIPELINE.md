## Jednopoleceniowe uruchomienie wszystkich plików

Umieść wszystkie pliki wejściowe bezpośrednio w `work/evidence`. Skrypty tworzą nową sesję UTC w `work/results`, a następnie dla każdego obsługiwanego pliku uruchamiają kolejno analizę bazową, macierz dekoderów, eksport klatek, analizę audio, pakiet JPEG oraz pakiet wyników macierzy.

### Ubuntu bare metal z Quadro P600

```bash
./launchers/run_all_linux.sh
```

### MacBook Air M4

```bash
./launchers/run_all_macos.sh
```

### Windows 11, Lenovo X1 Carbon Intel 8. generacji z Quick Sync

Uruchamiaj natywnie w PowerShell, nie wewnątrz WSL:

```powershell
.\launchers\run_all_windows.ps1 `
  -Ffmpeg C:\ffmpeg\bin\ffmpeg.exe `
  -Ffprobe C:\ffmpeg\bin\ffprobe.exe
```

WSL może służyć do pracy z repozytorium, ale testy QSV i D3D11VA wykonuje skrypt Windows.

### Windows 11, H110 z Intel i3-6300 i GTX 960

```powershell
.\launchers\run_all_windows.ps1 `
  -Ffmpeg C:\ffmpeg\bin\ffmpeg.exe `
  -Ffprobe C:\ffmpeg\bin\ffprobe.exe
```

Skrypt Windows próbuje wszystkie istniejące profile programowe, Intel i NVIDIA. Niedostępne ścieżki pozostają odnotowane w wynikach macierzy.
