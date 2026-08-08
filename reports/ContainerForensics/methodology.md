# ContainerForensics — Methodology

**Tool:** ContainerForensics 0.2.0
**Python:** 3.12.13
**Dependencies:** click=8.4.2, colorama=0.4.6, dateutil=2.9.0.post0, graphviz=0.21, jinja2=3.1.6, pymediainfo=7.0.1, rich=15.0.0
**Device signature database:** v1.1.1 (updated 2026-05-22)
**Analysis date:** 2026-08-06 19:38:46 UTC
**Input file:** 1796.mp4
**Input SHA-256:** 8560a2d703c1025ba7c5b4deef5e53f89b9ee0c1026cae67b4145e34d137a903

---

## Approach

ContainerForensics is a forensic triage instrument. It performs first-principles
binary parsing of the container structure against the published ISO/IEC 14496-12
specification to identify structural features that warrant further examination.
It does not authenticate media content. No decoder or
FFmpeg pass is used to derive the structural findings; the box/atom tree is read
directly from the file bytes so that every finding is traceable to a specific
field at a specific file offset.

The input file is hashed (SHA-256) before any analysis and is opened read-only.
The tool never writes to, moves, or modifies the input file.

## Checks performed

### Atom structure (Module 2)
- **A1** Required-box presence (ftyp, moov, mdat) — ISO/IEC 14496-12 §4.3, §8.1, §8.2
- **A2** moov / mdat ordering — ISO/IEC 14496-12 §8.2; Hall (2015)
- **A3** ftyp brand consistency — ISO/IEC 14496-12 §4.3
- **A4** Track-structure integrity — ISO/IEC 14496-12 §8.4.3
- **A5** Unexpected box types — ISO/IEC 14496-12; Hall (2015)

### Edit list (Module 3)
- **E1** Edit-list presence — ISO/IEC 14496-12 §8.6.6; Hall (2015)
- **E2** Edit-list entry count — Hall (2015)
- **E3** Empty-edit detection — Hall (2015)
- **E4** Edit-list timing consistency — ISO/IEC 14496-12 §8.6.6; Hall (2015)

### Chunk offsets (Module 4)
- **O1** Offset-table type (stco/co64) — ISO/IEC 14496-12 §8.7.5
- **O2** Offset monotonicity — ISO/IEC 14496-12 §8.7.5; Hall (2015)
- **O3** Offset gap analysis — ISO/IEC 14496-12 §8.7.5; Hall (2015)
- **O4** Offset vs. mdat alignment — ISO/IEC 14496-12 §8.1.1, §8.7.5
- **O5** Video/audio interleaving — ISO/IEC 14496-12; Hall (2015)

### Metadata (Module 5)
- **M1** Timestamp internal consistency — ISO/IEC 14496-12; SWGDE Technical Overview
- **M2** Timescale consistency — ISO/IEC 14496-12 §8.2.2, §8.4.2
- **M3** Duration consistency — ISO/IEC 14496-12 §8.2.2, §8.3.2, §8.4.2; Hall (2015)
- **M4** Codec-parameter consistency — ISO/IEC 14496-12 §8.5.2
- **M5** Encoder software identification — ISO/IEC 14496-12 §8.10; Hall (2015)

### Device match (Module 6)
- **D0–D2** Container-signature comparison against the device signature database.

## References

- Hall, C. (2015). *Analysis of MP4 Container File Format Forensics.* University of Denver.
- ISO/IEC 14496-12. *Base Media File Format Specification.*
- SWGDE *Technical Overview of Digital Video Files.*
- SWGDE *Best Practices for Data Acquisition from Digital Video Recorders.*
- SWGDE *Establishing Confidence in Digital and Multimedia Evidence Forensic Results.*

---

**ContainerForensics is a triage instrument. Its findings identify structural
features that warrant further examination by a qualified forensic examiner. A
triage finding does not constitute an authentication opinion and should not be
presented as one.**