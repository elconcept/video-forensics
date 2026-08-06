# Step 56: Debian/Ubuntu GPU-aware pipeline selection

The Debian-family launcher now inventories GPU controllers through `lspci`, render nodes through `/dev/dri/renderD*`, NVIDIA availability through `nvidia-smi`, and accelerator names through `ffmpeg -hwaccels`.

It selects:

- software single-thread and automatic-thread on every host
- CUDA/NVDEC when an active NVIDIA device, `nvidia-smi`, and FFmpeg CUDA are available
- VAAPI when a render node and FFmpeg VAAPI are available; `vainfo` is used when installed
- QSV when an Intel GPU, render node, and FFmpeg QSV are available

The session records `linux_gpu_inventory.json`, including WSL detection, GPU vendors, render nodes, FFmpeg accelerators, usable backends, and selected profiles. The bootstrap additionally attempts to install `pciutils` and `vainfo` through APT.
