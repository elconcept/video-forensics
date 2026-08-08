# Step 86 v2: decouple shared HEVC models from the legacy POC parser

The first executor incorrectly treated method parameters and local variables as external class dependencies. Version 2 performs lexical binding analysis and excludes function arguments, local assignments, comprehension targets, class members, and Python builtins.

It extracts `BitReader`, `SPS`, and `PPS` into `hevc_models.py`, rewrites direct consumers, and keeps compatibility re-exports in `hevc_poc.py`. It still aborts on genuine unhandled external dependencies or unsupported multiline imports.
