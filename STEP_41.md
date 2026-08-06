# Step 41: static connected regions during global frame change

This step implements `static_region_with_moving_frame` as a decoded-frame screening module.

For every consecutive image pair it computes:

- full-frame mean absolute change
- fraction of exactly identical grayscale pixels
- four-connected, bit-identical regions above a configurable size
- bounding boxes and pixel counts

A finding is emitted only when global MAE exceeds the configured threshold and at least one sufficiently large connected region remains bit-identical.

The finding retains ordinary explanations such as overlays, masks, compression plateaus, or genuinely static scene content. Because the analysis is pixel-domain, its output remains decoder-dependent when reference concealment is present.

Apply the entry point once:

python3 pyproject.patch.py
rm pyproject.patch.py
