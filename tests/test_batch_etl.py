import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from sistema_batch_etl import clean_and_transform, filter_new_records, REQUIRED_COLUMNS


def sample_row(detection_id="abc", timestamp_sec=12.4):
    row = {col: 0 for col in REQUIRED_COLUMNS}
    row.update(
        {
            "detection_id": detection_id,
            "source_type": "video",
            "source_id": "video_01.mp4",
            "frame_number": 25,
            "local_object_id": 1,
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.95,
            "x_min": 10,
            "y_min": 10,
            "x_max": 50,
            "y_max": 80,
            "width": 40,
            "height": 70,
            "area_pixels": 2800,
            "frame_width": 640,
            "frame_height": 480,
            "bbox_area_ratio": 0.01,
            "center_x": 30,
            "center_y": 45,
            "center_x_norm": 0.2,
            "center_y_norm": 0.3,
            "position_region": "top-left",
            "dominant_color_name": "black",
            "dom_r": 0,
            "dom_g": 0,
            "dom_b": 0,
            "timestamp_sec": timestamp_sec,
            "fps": 30.0,
            "ingestion_date": "2026-01-01 10:00:00",
            "has_backpack": False,
            "has_cellphone": False,
            "nearby_objects_count": 0,
        }
    )
    return row


def test_clean_transform_window_10_seconds():
    df = pd.DataFrame([sample_row(timestamp_sec=12.4)])
    out = clean_and_transform(df)
    assert int(out.iloc[0]["batch_window_start"]) == 10
    assert int(out.iloc[0]["batch_window_end"]) == 20


def test_filter_new_records():
    df = pd.DataFrame([sample_row(detection_id="a"), sample_row(detection_id="b")])
    out = clean_and_transform(df)
    new = filter_new_records(out, {"a"})
    assert list(new["detection_id"]) == ["b"]
