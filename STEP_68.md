# Step 68: pinned h265nal bootstrap and cross-platform CMake build

This step continues the parser migration by adding one bootstrap command used by Linux, macOS, and Windows launchers.

The bootstrap:

- requires Git, CMake, and a C++ compiler
- checks out `third_party/h265nal` from the configured upstream
- resolves the pinned revision to a full 40-character commit
- checks out that exact detached commit
- builds h265nal with CMake in Release mode
- disables upstream tests and the Clang fuzzer for the runtime build
- locates the resulting binary on Linux, macOS, and Windows layouts
- writes `third_party/h265nal.lock.json` with the full commit, tool paths, source path, and binary path

The upstream repository documents CMake builds and provides a C++ parser/tool for Annex B H.265 streams. citeturn124search326

Generated source and build directories are ignored; the lock file remains trackable. The existing Python SPS/PPS parsers are not modified.
