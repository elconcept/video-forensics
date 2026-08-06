# Step 39: orchestrated orphan-recovery pipeline

This step combines the implemented reconstruction stages into one command:

1. build byte-exact controlled streams
2. decode every stream through single-threaded libavcodec
3. reject controlled streams that fail or still report missing references
4. compute the determination mask and median reconstruction
5. optionally compare against one or more external independent-decoder outputs
6. emit the structured finding only after independent verification is available

Without an external decoder output, recovery is retained as provisional and the verification and report stages remain `pending`.

Example:

video-forensics-orphan-pipeline source.h265 --plan plan.json --output results/orphan --external-decoder-root results/orphan_libde265 --host-profile results/host_profile.json

Apply the entry point once:

python3 pyproject.patch.py
rm pyproject.patch.py
