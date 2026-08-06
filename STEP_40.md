# Step 40: calibrated playback-divergence matching

This step implements the first playback-divergence module.

It:

- calibrates crop position and scale on one control screen frame with a known matching source frame
- freezes that crop for every disputed screen frame
- performs an unconstrained search across all supplied extracted and recovered candidate frames
- reports best match, runner-up, NCC margin, and candidate count

Candidate directories should separate sources, for example `standard/` and `recovered/`. The module does not accept a narrow candidate window as proof and does not yet implement blend fitting. Blend models and their mandatory unconstrained control search remain a later stage.

Apply the entry point once:

python3 pyproject.patch.py
rm pyproject.patch.py
