# Step 47: persistent static-region series and review crops

This step extends the static-region detector with temporal persistence.

It links candidate regions across consecutive frame pairs by bounding-box intersection over union and reports:

- start and end frame
- series length in consecutive pairs
- union bounding box
- minimum and maximum global MAE
- every contributing region
- lossless PNG review crops with the union box marked in red

The output addresses the remaining review requirement for series length and human-readable cutouts. It retains ordinary explanations and does not claim that a persistent region was inserted.
