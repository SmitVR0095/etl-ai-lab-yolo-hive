import sys
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from yolo_features import safe_bbox_metrics, position_region, make_detection_id, dominant_color, build_record


def test_safe_bbox_metrics_division_by_zero():
    area, ratio = safe_bbox_metrics(10, 20, 0, 480)
    assert area == 200
    assert ratio == 0.0


def test_position_region_center():
    assert position_region(0.5, 0.5) == "middle-center"


def test_detection_id_is_deterministic():
    first = make_detection_id("video_01.mp4", 10, 2, 0)
    second = make_detection_id("video_01.mp4", 10, 2, 0)
    assert first == second
    assert len(first) == 32


def test_dominant_color_red_bgr_frame():
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    frame[:, :] = (0, 0, 255)
    color_name, r, g, b = dominant_color(frame, 0, 0, 20, 20)
    assert color_name == "red"
    assert (r, g, b) == (255, 0, 0)


def test_build_record_basic_values():
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    rec = build_record(
        frame_bgr=frame,
        source_type="image",
        source_id="imagen_01.jpg",
        frame_number=0,
        local_object_id=1,
        class_id=0,
        class_name="person",
        confidence=0.9,
        xyxy=(10, 20, 60, 80),
        fps=0.0,
    )
    assert rec.width == 50
    assert rec.height == 60
    assert rec.area_pixels == 3000
    assert rec.source_id == "imagen_01.jpg"
