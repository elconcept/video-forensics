# Step 66: per-channel and whole-pixel determination fractions

This step separates channel-level determination from whole-pixel determination.

For each frame it now records:

- determined count and fraction for the red channel
- determined count and fraction for the green channel
- determined count and fraction for the blue channel
- determined count and fraction for the whole pixel

A channel is determined when its standard deviation is at or below the configured threshold. A whole pixel is determined only when all three RGB channels satisfy that condition.

The numerical output adds `frame_N_channel_determination_mask.npy` as an `HxWx3 uint8` array and includes it in the compressed NPZ archive. The existing whole-pixel mask remains an `HxW uint8` array.
