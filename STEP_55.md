# Step 55: exact `slice_segment_address` derivation and validation

This step replaces floating-point geometry helpers with exact integer derivation.

For each active SPS it derives:

- `CtbSizeY = 1 << CtbLog2SizeY`
- `PicWidthInCtbsY = Ceil(pic_width_in_luma_samples / CtbSizeY)`
- `PicHeightInCtbsY = Ceil(pic_height_in_luma_samples / CtbSizeY)`
- `PicSizeInCtbsY`
- fixed address width `CeilLog2(PicSizeInCtbsY)`

`slice_segment_address` is read as a fixed-width unsigned field only when the segment is not first in the picture. Unused binary code points greater than or equal to `PicSizeInCtbsY` are rejected. The parser also records raster CTB coordinates and complete geometry next to every segment.

The address identifies the starting CTU in raster order, consistent with HEVC decoder interfaces and FFmpeg's distinct `slice_segment_addr` field. citeturn101search269turn101search270turn101search271
