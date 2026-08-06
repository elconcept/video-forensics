# Step 8: duplicate-frame and repeated-sequence analysis

This stage decodes a deterministic 64 x 36 grayscale stream and calculates:

- SHA-256 for exact equality after normalization
- a 1152-bit horizontal difference hash for adjacent near-duplicates
- repeated exact frame sequences

The normalized stream is analytical data. Equality here does not mean that compressed source packets are byte-identical, and repeated imagery is not automatically proof of editing.

Apply CLI integration once:

python3 cli.patch.py
rm cli.patch.py

Outputs:

- `duplicates/fingerprints.json`
- `duplicates/findings.json`
- `duplicates/duplicates.json`
