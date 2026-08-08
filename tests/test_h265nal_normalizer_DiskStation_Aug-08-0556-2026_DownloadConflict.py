from __future__ import annotations

from video_forensics.native.h265nal_normalizer import normalize, parse_text

SAMPLE = """
nal_unit {
  offset: 0x00000004
  length: 23
  nal_unit_header {
    forbidden_zero_bit: 0
    nal_unit_type: 33
    nuh_layer_id: 0
    nuh_temporal_id_plus1: 1
  }
  nal_unit_payload {
    sps {
      sps_seq_parameter_set_id: 0
      pic_width_in_luma_samples: 1920
      pic_height_in_luma_samples: 1080
    }
  }
}
nal_unit {
  offset: 0x00000020
  length: 7
  nal_unit_header { nal_unit_type: 34 nuh_layer_id: 0 nuh_temporal_id_plus1: 1 }
  nal_unit_payload { pps { pps_pic_parameter_set_id: 0 } }
}
"""


def test_parses_nested_h265nal_text() -> None:
    objects = parse_text(SAMPLE)
    assert len(objects) == 2
    assert objects[0]["value"]["offset"] == 4
    assert objects[0]["value"]["nal_unit_header"]["nal_unit_type"] == 33


def test_normalizes_stable_nal_schema() -> None:
    result = normalize(
        {
            "backend": "h265nal",
            "success": True,
            "input": "/evidence/a.h265",
            "command_contract": "annex_b_full_file_text",
            "stdout": SAMPLE,
        }
    )
    assert result["primary_backend"] == "h265nal"
    assert result["nal_count"] == 2
    assert result["nal_units"][0]["nal_unit_type"] == 33
    assert result["nal_units"][1]["nal_unit_type"] == 34
