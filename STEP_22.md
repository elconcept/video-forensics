# Step 22: normalized cross-decoder frame comparison

Exact framemd5 output may differ because hardware paths can expose different pixel formats, ranges, or conversion behavior. This step adds a second comparison layer.

Each decoder output is normalized to:

- grayscale
- 192 x 108
- area scaling
- SHA-256 per normalized frame

The comparison then reports the first normalized frame divergence and frame-count differences.

This does not yet calculate NCC or MAD. Exact normalized equality is a strict first test; perceptual comparison is the next milestone.
