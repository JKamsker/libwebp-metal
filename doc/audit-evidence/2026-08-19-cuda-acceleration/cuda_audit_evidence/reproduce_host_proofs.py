#!/usr/bin/env python3
"""CPU-only proofs for deterministic CUDA backend contract defects."""
from __future__ import annotations
import json
from dataclasses import dataclass


def decimate_flag(value: str | None, default: bool = True) -> bool:
    return default if value is None or value == "" else value != "0"


def main_flag(value: str | None, default: bool = True) -> bool:
    if value is None or value == "":
        return default
    return value.lower() not in {"0", "false", "no"}


def band_proof(mb_w: int, mb_h: int, band_count: int):
    rows_per_band = (mb_h + band_count - 1) // band_count
    last_diagonal = (mb_w - 1) + 2 * (mb_h - 1)
    records = []
    for band in range(band_count):
        end_raw = (band + 1) * rows_per_band
        end_row = min(end_raw, mb_h)
        target_d = (mb_w - 1) + 2 * (end_row - 1)
        row_start = band * rows_per_band
        row_end = min(row_start + rows_per_band, mb_h)
        records.append({
            "band": band,
            "row_start": row_start,
            "row_end": row_end,
            "rows": row_end - row_start,
            "target_diagonal": target_d,
            "target_within_launches": 0 <= target_d <= last_diagonal,
        })
    # The implementation breaks after recording the first matching band on a
    # diagonal, so duplicate target diagonals leave later bands unrecorded.
    seen = set()
    for r in records:
        r["event_recorded"] = r["target_within_launches"] and r["target_diagonal"] not in seen
        if r["event_recorded"]:
            seen.add(r["target_diagonal"])
    return {"mb_w": mb_w, "mb_h": mb_h, "band_count": band_count,
            "rows_per_band": rows_per_band, "last_diagonal": last_diagonal,
            "bands": records}


def stride_proof(width: int, height: int, caller_stride: int):
    tight = bytes(range(1, width * height + 1))
    caller = bytearray([0xEE] * (caller_stride * height))
    # Current implementation: one flat memcpy of width*height bytes.
    caller[:len(tight)] = tight
    actual_rows = [list(caller[y * caller_stride:(y + 1) * caller_stride])
                   for y in range(height)]
    expected = bytearray([0xEE] * (caller_stride * height))
    for y in range(height):
        expected[y * caller_stride:y * caller_stride + width] = tight[y * width:(y + 1) * width]
    expected_rows = [list(expected[y * caller_stride:(y + 1) * caller_stride])
                     for y in range(height)]
    return {"width": width, "height": height, "caller_stride": caller_stride,
            "actual_rows": actual_rows, "expected_rows": expected_rows,
            "equal": actual_rows == expected_rows}


def transactional_proof():
    out = {"results": "sentinel", "recon_y": "sentinel", "recon_u": "sentinel", "recon_v": "sentinel"}
    # Current whole-pass sequence writes each caller buffer before the final sync.
    out["results"] = "modified"
    out["recon_y"] = "modified"
    # Model a later cudaMemcpyAsync failure before U/V and final sync.
    returned = "WEBP_ACCELERATOR_ERROR"
    return {"returned": returned, "outputs_after_error": out,
            "transactional_contract_satisfied": all(v == "sentinel" for v in out.values())}


result = {
    "env_parser": {v: {"main": main_flag(v), "decimate": decimate_flag(v)}
                   for v in [None, "", "0", "false", "FALSE", "no", "1"]},
    "empty_band_example": band_proof(mb_w=80, mb_h=17, band_count=8),
    "padded_stride_example": stride_proof(width=4, height=3, caller_stride=7),
    "transactional_sequence_example": transactional_proof(),
}
print(json.dumps(result, indent=2))
