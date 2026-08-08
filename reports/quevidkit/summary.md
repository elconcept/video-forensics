# Technical Forensic Report for LLM Analysis

## 1. Evidence Metadata
* **File Path**: `/home/tom/projects/quevidkit/work/evidence/1796.mp4`
* **SHA256 Hash**: `8560a2d703c1025ba7c5b4deef5e53f89b9ee0c1026cae67b4145e34d137a903`
* **File Size**: 2193408 bytes
* **Duration**: 15.669 seconds (15.67s)
* **Analysis Start Time (UTC)**: 2026-08-06T22:07:01.829255+00:00
* **Analysis End Time (UTC)**: 2026-08-06T22:07:04.071360+00:00

## 2. Summary of Findings
* **Verdict / Label**: TAMPERED
* **Tamper Probability**: 83.61% (83.6%)
* **Evidence Confidence**: 90.44% (90.4%)
* **Overall Assessment**: 7 out of 15 checks returned strong anomaly signals. Anomalies were detected simultaneously across 4 independent forensic categories: audio, codec, metadata, and quality. This multi-category correlation significantly reduces the probability of a false positive.

## 3. Technical Findings & Ujawnione Artefakty (Correlated)

### 3.1 Metadata Category
* **Check**: `metadata_codec_consistency`
* **Score/Confidence**: 81.83% / 85.0%
* **Finding**: Audio/video duration mismatch.
* **Details**: `audio_video_duration_diff_s` is 2.805 seconds.
* **Interpretation**: Indicates potential re-muxing, trimming, or splicing without proper container header updates.

### 3.2 Codec Category
* **Check**: `qp_consistency`
* **Score/Confidence**: 100.0% / 55.0%
* **Finding**: GOP type pattern inconsistency.
* **Details**: 2 out of 3 total GOPs display a non-dominant pattern (`anomaly_rate`: 0.6667). Suspicious segments found between 3.40s - 7.40s and 7.40s - 9.399s.
* **Correlations**: Corroborated by `compression_consistency` and `double_compression_detection`.

* **Check**: `double_compression_detection`
* **Score/Confidence**: 57.43% / 73.8%
* **Finding**: Periodic pattern at lag 138 suggests prior encoding with a different GOP (current GOP is 51).
* **Details**: Analysis of I-frame size periodicity and P-frame autocorrelation indicates re-encoding over previously compressed video.

* **Check**: `compression_consistency`
* **Score/Confidence**: 54.63% / 51.92%
* **Finding**: P-frame size shifts detected in windows 0, 1, and 2.

### 3.3 Audio Category
* **Check**: `audio_spectral_continuity`
* **Score/Confidence**: 84.61% / 55.72%
* **Finding**: Multiple abrupt audio spectral discontinuities.
* **Details**: Energy discontinuity at 0.00s (z=21.45); spectral centroid discontinuities at 0.00s, 3.80s, 8.35s, 12.45s; zero-crossing rate (ZCR) discontinuities at 12.45s, 12.50s, 12.55s.

### 3.4 Quality Category
* **Check**: `temporal_noise_consistency`
* **Score/Confidence**: 85.25% / 45.6%
* **Finding**: Multiple noise floor and high-frequency energy shifts.
* **Details**: Substantial shifts noted at 0.5s (z=13.46), 1.6s (z=26.4), 2.1s (z=8.78), and ~9.09s (z=40.91).
* **Correlations**: Corroborated by `ela_frame_analysis`.

* **Check**: `ela_frame_analysis` (Error Level Analysis)
* **Score/Confidence**: 81.3% / 41.0%
* **Finding**: `ela_mean` and `ela_std` shifts across the timeline.
* **Details**: Significant shifts at 0.7s (z=6.25), 1.3s (z=4.06), and 12.6s (z=12.09).

## 4. Red Flags & Anomalies (Czerwone flagi)
* **Missing/Failed Data**: The `frame_quality_shift` check failed and was skipped.
* **Error Log**: `opencv_frame_quality_checks: operands could not be broadcast together with shapes (180,40) (180,39)`.
* **Interpretation of Tampering**: The convergence of audio spectral breaks, noise shifts, ELA shifts, and GOP pattern anomalies within a single file strongly points to manipulation (splicing or joining of segments encoded by different software/hardware) rather than benign re-encoding.