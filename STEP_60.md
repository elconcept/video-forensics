# Step 60: h265nal primary backend and migration gate

Step 59 did not complete the migration DoD. It only built an adapter around the upstream text dump. Step 60 fixes a payload-normalization defect, adds local-binary discovery, makes h265nal output the primary syntax source, tracks parameter-set versions, assigns active PPS/SPS versions to pictures, derives POC, detects non-IRAP regression, and blocks automatic orphan-plan generation on parse errors or legacy disagreement.

The remaining migration gaps are recorded explicitly in `MIGRATION_DOD.md`; they are not reported as complete.
