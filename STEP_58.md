# Step 58: complete base-layer HEVC PPS parser

This step replaces the early PPS parser with a complete base-layer parser through the PPS extension section.

It records dependent-slice and output flags, extra slice-header bits, CABAC and sign-data-hiding flags, default active reference counts, initial QP, transform skip and CU QP delta controls, chroma offsets, weighted prediction, transquant bypass, tiles, entropy-coding synchronization, loop-filter behavior, deblocking controls and derived offsets, scaling-list presence, list modification, parallel merge level, slice-header extensions, and PPS range-extension values.

Multilayer, 3D, SCC, and unknown extension payloads are identified but retained as unparsed extension bits. FFmpeg's PPS structure exposes these base fields, tile geometry, deblocking controls, range-extension offsets and extension flags. citeturn109search96turn109search97turn109search98
