# Step 83: resolve SPS-owned RPS into legacy slice comparison

The real reference result shows that legacy already parses the applicable short-term RPS in SPS: one negative picture and zero positive pictures. h265nal reports that each non-IRAP slice selects the SPS RPS through `short_term_ref_pic_set_sps_flag = 1`.

This step enriches each legacy slice by resolving `slice.pps_id -> PPS.sps_id -> SPS.short_term_ref_pic_sets[0]`. It exports the three missing canonical fields on the matching slice record:

- `short_term_ref_pic_set_sps_flag`
- `num_negative_pics`
- `num_positive_pics`

No value is invented: all values come from parsed legacy PPS/SPS structures and the slice's recorded PPS identifier.

The legacy-removal decision is also made consistent with enrollment: successful FFmpeg control, semantic agreement, and complete applicable RPS coverage are all required.
