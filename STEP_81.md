# Step 81: applicability-aware RPS completeness

The real `1796.mp4` comparison reached enrollment but failed the RPS completeness gate. The previous rule incorrectly required every canonical short-term and long-term RPS field to occur in one stream, although HEVC RPS syntax is conditional and mutually exclusive in several branches.

This step changes the gate from absolute vocabulary coverage to stream applicability:

- collect RPS fields actually emitted by either backend for this stream
- require every applicable field to exist in both backends
- do not require conditionally absent syntax
- report exact applicable, shared, missing-primary and missing-legacy field sets
- require at least one applicable RPS field before declaring completeness

The broad category coverage report remains available as diagnostic information, but no longer determines migration acceptance.
