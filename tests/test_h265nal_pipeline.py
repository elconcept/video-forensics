from __future__ import annotations

import stat
from pathlib import Path

from video_forensics.native.h265nal_pipeline import run_pipeline

DUMP = """h265nal: original version
nal_unit {
  offset: 0x00000004
  length: 8
  nal_unit_header {
    nal_unit_type: 33
  }
  sps {
    sps_seq_parameter_set_id: 0
    log2_max_pic_order_cnt_lsb_minus4: 4
  }
}
nal_unit {
  offset: 12
  length: 8
  nal_unit_header {
    nal_unit_type: 34
  }
  pps {
    pps_pic_parameter_set_id: 0
    pps_seq_parameter_set_id: 0
  }
}
nal_unit {
  offset: 20
  length: 9
  nal_unit_header {
    nal_unit_type: 19
  }
  nal_unit_payload {
    slice_segment_layer {
      slice_segment_header {
        first_slice_segment_in_pic_flag: 1
        slice_pic_parameter_set_id: 0
        slice_type: 2
      }
    }
  }
}
"""


def fake_binary(path: Path) -> None:
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"sys.stdout.write({DUMP!r})\n",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_end_to_end_pipeline_with_cli_binary(tmp_path: Path) -> None:
    stream = tmp_path / "input.h265"
    stream.write_bytes(b"annex-b-fixture")
    binary = tmp_path / "h265nal"
    fake_binary(binary)
    result = run_pipeline(
        stream,
        tmp_path / "output",
        h265nal=str(binary),
        python="python",
        legacy_json=None,
        timeout=30,
    )
    assert result["status"] == "completed"
    assert result["picture_count"] == 1
    assert result["parse_error_count"] == 0
    assert (tmp_path / "output" / "h265nal_raw" / "stdout.txt").is_file()
    assert (tmp_path / "output" / "primary" / "pictures.csv").is_file()
