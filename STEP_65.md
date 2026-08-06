# Step 65: numerical per-pixel recovery arrays

This step writes recovery values in machine-readable numerical formats in addition to visual PNG derivatives.

For every aligned controlled frame it writes:

- `frame_N_median.npy`: per-channel median, `float32`
- `frame_N_stddev.npy`: population standard deviation per channel, `float32`
- `frame_N_determination_mask.npy`: binary per-pixel determination mask, `uint8`
- `frame_N.npz`: compressed archive containing all three arrays

`index.csv` and `manifest.json` record shapes, dtypes, determined-pixel counts and fractions, filenames, and SHA-256 values. The orphan pipeline invokes this stage automatically using the same sigma threshold as the visual recovery stage.
