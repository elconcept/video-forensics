# Step 75: canonical RPS and slice field parity surface

This step creates a canonical field vocabulary across h265nal and legacy output.

It normalizes aliases for:

- SPS and PPS identifiers and coded dimensions
- core slice fields and POC LSB
- explicit and predicted short-term RPS fields
- negative and positive delta-POC arrays
- used and use-delta arrays
- SPS-selected and slice-defined long-term references
- long-term POC-LSB, used flags, MSB-present flags, and cycle values

The semantic comparison now reports coverage separately for parameter sets, core slice fields, short-term RPS, and long-term RPS. `rps_comparison_complete` becomes true only when every defined canonical short-term and long-term RPS field is shared by both compared backends.

h265nal includes dedicated SPS, PPS, slice, and short-term reference-picture-set parsers. citeturn136search315turn136search316
