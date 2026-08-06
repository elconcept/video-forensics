# Step 67: enforceable HEVC parser migration gate

Step 61 does not satisfy the migration Definition of Done. It adds libde265 decoder manifests, while the migration plan concerns h265nal source pinning, a C++ JSON wrapper, cross-platform CMake builds, launcher bootstrap, parser authority, backend comparison, independent control, and eventual legacy removal.

This step converts the supplied migration plan into an executable repository audit. The gate checks:

- pinned `third_party/h265nal` gitlink commit
- C++ stable-JSON wrapper
- CMake build definition
- compiler and CMake bootstrap in all OS launchers
- h265nal adapter and pipeline
- explicit h265nal primary-backend policy
- legacy SPS/PPS comparison-only policy
- reference comparison involving h265nal, legacy and FFmpeg
- independent corroboration for high-severity conclusions
- final legacy-removal state

The gate exits with status 1 until every migration condition passes and writes a structured JSON checklist. It does not modify `hevc_sps.py` or `hevc_pps.py`.
