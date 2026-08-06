# Step 55: Windows GPU-aware pipeline selection

The Windows launcher now inventories active display controllers through `Win32_VideoController`, optionally confirms present devices through `Get-PnpDevice`, records driver and PNP identifiers, reads the hardware accelerators exposed by the selected FFmpeg build, and selects every matching decoder profile.

Selection rules:

- software profiles always run
- Intel GPU plus FFmpeg QSV enables Intel QSV
- Intel GPU plus FFmpeg D3D11VA enables Intel D3D11VA
- NVIDIA GPU plus FFmpeg CUDA enables NVIDIA CUDA/NVDEC
- NVIDIA GPU plus FFmpeg D3D11VA enables NVIDIA D3D11VA
- AMD GPU plus FFmpeg D3D11VA enables an AMD profile when that profile exists

The session stores `windows_gpu_inventory.json` and `ffmpeg_hwaccels.json`. Profile selection does not itself prove successful hardware decoding; each selected profile still has to complete and preserve its FFmpeg diagnostics.
