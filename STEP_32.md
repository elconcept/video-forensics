# Step 32: complete visual frame export per decoder

This step exports every frame returned by every selected decoder profile into two parallel trees:

- `lossless/<host_profile_id>__<decoder>/` as full-resolution PNG
- `email/<host_profile_id>__<decoder>/` as resized JPEG review copies

Both trees contain an index with SHA-256 and size for each derivative image, plus the complete decoder log. The root manifest records the source SHA-256, host profile, exact commands, frame counts, and export policy.

The compressed tree includes a Polish notice stating that it contains review copies, lossless PNG derivatives are retained for delivery on request, and the source recording remains the primary material.

Usage example:

video-forensics-export-visual-frames input.mp4 --host-profile results/host_profile.json --profile profiles/decoder_matrix/software_single_thread.json --profile profiles/decoder_matrix/windows_intel_qsv.json --output results/visual_frames

Hardware profiles that fail remain documented through return codes and stderr; their directories are not silently presented as successful decoder output.

Apply the entry point once:

python3 pyproject.patch.py
rm pyproject.patch.py
