# Step 60: order-preserving libde265 YUV-to-PNG conversion

This step replaces one-stream YUV conversion with an explicit frame-by-frame mapping.

The converter:

- computes the exact raw byte size of one frame
- rejects partial trailing frames
- reads YUV frames sequentially without seeking or reordering
- invokes FFmpeg separately for each raw frame with `-frames:v 1`
- names PNG N from raw source index N-1
- records source offset, source-frame SHA-256, PNG SHA-256, and sizes
- verifies a contiguous PNG filename sequence
- verifies that PNG count equals the libde265 raw-frame inventory

This avoids frame synchronization, timestamp, duplication, and dropping logic during conversion. FFmpeg requires rawvideo geometry and pixel format to interpret uncontainerized input, and option order applies options to the following input or output. citeturn110search333turn110search334turn110search335

Output per variant: `frames/index.csv` and `frames/yuv_png_sequence.json`.
