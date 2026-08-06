# Step 50: compressed email-submission bundle with lossless retention record

This step packages the compressed visual-review derivatives for electronic submission without silently discarding the lossless set.

Before creating the ZIP it verifies:

- identical decoder-run sets in `email/` and `lossless/`
- exact agreement between each directory and its `index.csv`
- size and SHA-256 of every JPEG and PNG derivative

The ZIP contains only compressed JPEG review copies, their indexes, decoder logs, a Polish notice, and a submission manifest. The manifest records the retained lossless frame count, lossless-index SHA-256, and retained directory for every decoder run.

An external SHA-256 file is written for the submission ZIP. Lossless PNG files remain outside this email bundle and can be supplied separately on request.
