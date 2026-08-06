# Step 57: complete base-layer HEVC SPS parser

This step replaces the early SPS parser with a complete base-layer parser through the end of the SPS RBSP.

It records profile-tier-level data, chroma format, dimensions, conformance window, bit depths, POC width, sub-layer ordering, coding and transform block geometry, scaling-list presence, AMP, SAO, PCM, all SPS short-term reference picture sets, long-term references, temporal MVP, strong intra smoothing, VUI timing/HRD restrictions, range extensions, and derived CTB geometry.

Multilayer, 3D, SCC, and unknown extension payloads are identified but retained as unparsed extension bits. They are not silently interpreted as base-layer syntax.

FFmpeg's SPS structure explicitly includes ordering, scaling, short- and long-term reference sets, PCM, VUI, coding-block geometry and extension-related fields, which are now represented in the project output. citeturn108search81turn108search75turn108search76turn108search78
