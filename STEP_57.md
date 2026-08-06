# Step 57: long-term reference pictures from SPS and slice headers

This step parses SPS-declared and slice-declared long-term references.

It records:

- `long_term_ref_pics_present_flag`
- `num_long_term_ref_pics_sps`
- SPS POC-LSB values and used-by-current flags
- `num_long_term_sps` and `num_long_term_pics`
- `lt_idx_sps`
- explicit `poc_lsb_lt`
- used-by-current flags
- `delta_poc_msb_present_flag`
- raw and cumulative `delta_poc_msb_cycle_lt`
- whether each reference came from SPS or the slice header

Counts and indices are range-checked against the active SPS and the 32-entry HEVC reference limit. FFmpeg exposes SPS long-term POC-LSB arrays and a `LongTermRPS` structure with POC, MSB-presence, used flags, and reference count. citeturn107search322turn107search323turn107search326

Output: `long_term_rps.json`, with the active long-term set embedded in each independent slice-segment record.
