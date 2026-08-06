# Step 23: perceptual cross-decoder comparison

This step preserves normalized grayscale frames and compares every pair of decoder runs using:

- mean absolute error
- root mean square error
- normalized cross-correlation
- fraction of identical pixels

It also reports missing frames and the first position where normalized outputs differ.

The stored `.gray` files are derivative analytical frames at 192 x 108, not source evidence.
