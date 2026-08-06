# Step 20: native Windows decoder matrix

The decoder matrix runs directly in Python on Windows. Docker is not used for the hardware-decoder runs.

Target machines:

- Lenovo X1 Carbon, 8th-generation Core i5: software, Intel QSV, Intel D3D11VA
- desktop i3-6300 plus GTX 960: software, NVIDIA D3D11VA, NVIDIA CUDA/NVDEC

Every run stores the input hash, complete command, FFmpeg inventories, Windows video-controller inventory, stderr, stdout, and a framemd5 file.

The scripts do not assume that a requested backend actually succeeded. The manifest and stderr must be reviewed, especially adapter selection and decoder errors.
