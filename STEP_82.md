# Step 82: align semantic records by NAL identity

The real `1796.mp4` diagnostic proves that both parsers emit 260 NAL units in exactly the same NAL-type order. The 221 reported field mismatches were caused by comparing separately grouped semantic records by list index. The legacy exporter groups SPS, PPS and slices, while h265nal preserves stream order.

This step replaces positional comparison with identity alignment on `(nal_number, kind)`.

It also:

- reports missing records explicitly
- prevents absent VPS support in legacy from shifting all later records
- derives shared-field coverage from the aligned record itself
- removes raw semantic-list length equality as an agreement condition
- retains missing non-VPS records as a failure

This corrects the comparison model without weakening field equality or RPS requirements.
