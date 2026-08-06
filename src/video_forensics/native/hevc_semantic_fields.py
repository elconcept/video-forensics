from __future__ import annotations

import re
from typing import Any

INDEX = re.compile(r"\[(\d+)\]")
ALIASES = {
    "slice_pic_parameter_set_id": "pps_id",
    "pps_pic_parameter_set_id": "pps_id",
    "pps_id": "pps_id",
    "pps_seq_parameter_set_id": "sps_id",
    "sps_seq_parameter_set_id": "sps_id",
    "sps_id": "sps_id",
    "pic_width_in_luma_samples": "width",
    "width": "width",
    "pic_height_in_luma_samples": "height",
    "height": "height",
    "slice_pic_order_cnt_lsb": "poc_lsb",
    "pic_order_cnt_lsb": "poc_lsb",
    "poc_lsb": "poc_lsb",
    "first_slice_segment_in_pic_flag": "first_slice_segment_in_pic_flag",
    "dependent_slice_segment_flag": "dependent_slice_segment_flag",
    "slice_segment_address": "slice_segment_address",
    "slice_type": "slice_type",
    "short_term_ref_pic_set_sps_flag": "short_term_ref_pic_set_sps_flag",
    "short_term_ref_pic_set_idx": "short_term_ref_pic_set_idx",
    "num_negative_pics": "num_negative_pics",
    "num_positive_pics": "num_positive_pics",
    "inter_ref_pic_set_prediction_flag": "inter_ref_pic_set_prediction_flag",
    "delta_idx_minus1": "delta_idx_minus1",
    "delta_rps_sign": "delta_rps_sign",
    "abs_delta_rps_minus1": "abs_delta_rps_minus1",
    "num_long_term_sps": "num_long_term_sps",
    "num_long_term_pics": "num_long_term_pics",
    "lt_idx_sps": "lt_idx_sps",
    "poc_lsb_lt": "poc_lsb_lt",
    "used_by_curr_pic_lt_flag": "used_by_curr_pic_lt_flag",
    "delta_poc_msb_present_flag": "delta_poc_msb_present_flag",
    "delta_poc_msb_cycle_lt": "delta_poc_msb_cycle_lt",
}
ARRAY_ALIASES = {
    "delta_poc_s0_minus1": "delta_poc_s0_minus1",
    "used_by_curr_pic_s0_flag": "used_by_curr_pic_s0_flag",
    "delta_poc_s1_minus1": "delta_poc_s1_minus1",
    "used_by_curr_pic_s1_flag": "used_by_curr_pic_s1_flag",
    "used_by_curr_pic_flag": "used_by_curr_pic_flag",
    "use_delta_flag": "use_delta_flag",
    "lt_idx_sps": "lt_idx_sps",
    "poc_lsb_lt": "poc_lsb_lt",
    "used_by_curr_pic_lt_flag": "used_by_curr_pic_lt_flag",
    "delta_poc_msb_present_flag": "delta_poc_msb_present_flag",
    "delta_poc_msb_cycle_lt": "delta_poc_msb_cycle_lt",
}
CATEGORIES = {
    "parameter_sets": {"pps_id", "sps_id", "width", "height"},
    "slice_core": {
        "pps_id",
        "poc_lsb",
        "first_slice_segment_in_pic_flag",
        "dependent_slice_segment_flag",
        "slice_segment_address",
        "slice_type",
    },
    "short_term_rps": {
        "short_term_ref_pic_set_sps_flag",
        "short_term_ref_pic_set_idx",
        "num_negative_pics",
        "num_positive_pics",
        "inter_ref_pic_set_prediction_flag",
        "delta_idx_minus1",
        "delta_rps_sign",
        "abs_delta_rps_minus1",
        "delta_poc_s0_minus1",
        "used_by_curr_pic_s0_flag",
        "delta_poc_s1_minus1",
        "used_by_curr_pic_s1_flag",
        "used_by_curr_pic_flag",
        "use_delta_flag",
    },
    "long_term_rps": {
        "num_long_term_sps",
        "num_long_term_pics",
        "lt_idx_sps",
        "poc_lsb_lt",
        "used_by_curr_pic_lt_flag",
        "delta_poc_msb_present_flag",
        "delta_poc_msb_cycle_lt",
    },
}


def leaf_name(path: str) -> str:
    return path.rsplit(".", 1)[-1]


def canonical_key(path: str) -> str | None:
    leaf = leaf_name(path)
    plain = INDEX.sub("", leaf)
    index_match = INDEX.search(leaf)
    if index_match and plain in ARRAY_ALIASES:
        return f"{ARRAY_ALIASES[plain]}[{int(index_match.group(1))}]"
    if plain in ARRAY_ALIASES and path.endswith("._values"):
        return ARRAY_ALIASES[plain]
    return ALIASES.get(plain)


def canonicalize(fields: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for path, value in fields.items():
        key = canonical_key(path)
        if key is None:
            continue
        if isinstance(value, list):
            for index, item in enumerate(value):
                result[f"{key}[{index}]"] = item
        else:
            result[key] = value
    return result


def base_key(key: str) -> str:
    return INDEX.sub("", key)


def category_coverage(keys: set[str]) -> dict[str, dict[str, Any]]:
    bases = {base_key(key) for key in keys}
    result: dict[str, dict[str, Any]] = {}
    for category, expected in CATEGORIES.items():
        present = sorted(expected & bases)
        result[category] = {
            "present": present,
            "present_count": len(present),
            "expected_count": len(expected),
            "coverage_fraction": len(present) / len(expected),
        }
    return result
