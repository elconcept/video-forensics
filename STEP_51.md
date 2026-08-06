# Step 51: reviewed and source-bound orphan plans

Step 45 deliberately emits only `draft_requires_review`. This step closes the enforcement gap.

The review command:

- validates every selected NAL number against the Annex B stream
- confirms VPS/SPS/PPS, IDR, and orphan-range NAL types
- binds the approved plan to the exact Annex B SHA-256
- records reviewer, UTC timestamp, rationale, draft path, and draft SHA-256
- writes status `approved_for_controlled_reconstruction`

`orphan_stream_builder` is patched to reject drafts, plans without a source hash, and plans bound to a different Annex B stream.

Example:

`video-forensics-review-orphan-plan source.h265 --draft orphan_plan_draft.json --output orphan_plan_approved.json --reviewer "T. K." --rationale "NAL selections checked against poc_analysis.json and nal_units.csv"`

The approval confirms experimental byte selections. It does not prove that a candidate IDR is the historically removed reference picture.
