# Step 56: short-term reference picture sets from SPS and slice headers

This step parses explicit and inter-RPS-predicted short-term reference picture sets.

It records:

- `num_negative_pics` and `num_positive_pics`
- cumulative negative and positive delta POCs
- used-by-current-picture flags
- inter-RPS prediction flag
- `delta_idx_minus1`, reference-set index, delta sign and magnitude
- derived delta POCs for predicted sets
- syntax bit length
- SPS RPS list selection in slice headers
- explicit slice-header RPS when the SPS-selection flag is zero

The parser limits the aggregate short-term set to 16 references and rejects invalid set references. FFmpeg stores SPS short-term RPS arrays and a `ShortTermRPS` structure containing delta POCs, used flags, prediction state, reference index information, and negative/delta counts. citeturn105search288turn105search293turn105search299turn105search304

Output: `short_term_rps.json`, with the active set also embedded in each independent slice-segment record.
