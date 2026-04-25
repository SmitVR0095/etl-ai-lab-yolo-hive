"""Utilidades para extracción de atributos en detecciones YOLO.

Este módulo no depende de Ultralytics; por eso es fácil de probar con pytest.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


CSV_COLUMNS = [
    "detection_id", "source_type", "source_id", "frame_number", "local_object_id",
    "class_id", "class_name", "confidence", "x_min", "y_min", "x_max", "y_max",
    "width", "height", "area_pixels", "frame_width", "frame_height", "bbox_area_ratio",
    "center_x", "center_y", "center_x_norm", "center_y_norm", "position_region",
    "dominant_color_name", "dom_r", "dom_g", "dom_b", "timestamp_sec", "fps",
    "ingestion_date", "has_backpack", "has_cellphone", "nearby_objects_count",
]


@dataclass(frozen=True)
class DetectionRecord:
    """Representa una fila final del CSV de staging de detecciones."""

    detection_id: str
    source_type: str
    source_id: str
    frame_number: int
    local_object_id: int
    class_id: int
    class_name: str
    confidence: float
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    width: int
    height: int
    area_pixels: int
    frame_width: int
    frame_height: int
    bbox_area_ratio: float
    center_x: float
    center_y: float
    center_x_norm: float
    center_y_norm: float
    position_region: str
    dominant_color_name: str
    dom_r: int
    dom_g: int
    dom_b: int
    timestamp_sec: float
    fps: float
    ingestion_date: str
    has_backpack: bool
    has_cellphone: bool
    nearby_objects_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convierte el registro a diccionario serializable a CSV."""
        return asdict(self)


def safe_bbox_metrics(width: int, height: int, frame_width: int, frame_height: int) -> tuple[int, float]:
    """Calcula área del bbox y ratio respecto al frame, evitando división por cero."""
    area_pixels = max(int(width), 0) * max(int(height), 0)
    frame_area = int(frame_width) * int(frame_height)
    bbox_area_ratio = 0.0 if frame_area <= 0 else area_pixels / frame_area
    return area_pixels, float(bbox_area_ratio)


def position_region(center_x_norm: float, center_y_norm: float) -> str:
    """Clasifica la posición del centro del objeto en una grilla 3x3."""
    horizontal = "left" if center_x_norm < 1 / 3 else "center" if center_x_norm < 2 / 3 else "right"
    vertical = "top" if center_y_norm < 1 / 3 else "middle" if center_y_norm < 2 / 3 else "bottom"
    return f"{vertical}-{horizontal}"


def dominant_color(frame_bgr: np.ndarray, x_min: int, y_min: int, x_max: int, y_max: int) -> tuple[str, int, int, int]:
    """Obtiene el color dominante aproximado del ROI del objeto.

    Se usa el promedio RGB del recorte y una clasificación simple por cercanía a colores base.
    """
    h, w = frame_bgr.shape[:2]
    x1, y1 = max(0, x_min), max(0, y_min)
    x2, y2 = min(w, x_max), min(h, y_max)
    roi = frame_bgr[y1:y2, x1:x2]
    if roi.size == 0:
        return "unknown", 0, 0, 0

    mean_bgr = roi.reshape(-1, 3).mean(axis=0)
    b, g, r = [int(round(v)) for v in mean_bgr]
    color_name = nearest_color_name(r, g, b)
    return color_name, r, g, b


def nearest_color_name(r: int, g: int, b: int) -> str:
    """Asigna nombre de color por distancia euclidiana a una paleta base."""
    palette = {
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "gray": (128, 128, 128),
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "orange": (255, 165, 0),
        "purple": (128, 0, 128),
        "brown": (150, 75, 0),
    }
    rgb = np.array([r, g, b], dtype=float)
    return min(palette, key=lambda name: float(np.linalg.norm(rgb - np.array(palette[name], dtype=float))))


def make_detection_id(source_id: str, frame_number: int, local_object_id: int, class_id: int) -> str:
    """Genera una clave determinística para impedir duplicados entre re-ejecuciones."""
    raw = f"{Path(source_id).name}|{int(frame_number)}|{int(local_object_id)}|{int(class_id)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def build_record(
    *,
    frame_bgr: np.ndarray,
    source_type: str,
    source_id: str,
    frame_number: int,
    local_object_id: int,
    class_id: int,
    class_name: str,
    confidence: float,
    xyxy: tuple[float, float, float, float],
    fps: float,
    related_flags: dict[str, Any] | None = None,
) -> DetectionRecord:
    """Construye un registro enriquecido a partir de una caja YOLO."""
    frame_height, frame_width = frame_bgr.shape[:2]
    x_min, y_min, x_max, y_max = [int(round(v)) for v in xyxy]
    x_min, y_min = max(0, x_min), max(0, y_min)
    x_max, y_max = min(frame_width, x_max), min(frame_height, y_max)

    width = max(0, x_max - x_min)
    height = max(0, y_max - y_min)
    area_pixels, bbox_area_ratio = safe_bbox_metrics(width, height, frame_width, frame_height)
    center_x = x_min + width / 2
    center_y = y_min + height / 2
    center_x_norm = 0.0 if frame_width <= 0 else center_x / frame_width
    center_y_norm = 0.0 if frame_height <= 0 else center_y / frame_height
    color_name, dom_r, dom_g, dom_b = dominant_color(frame_bgr, x_min, y_min, x_max, y_max)
    flags = related_flags or {}

    return DetectionRecord(
        detection_id=make_detection_id(source_id, frame_number, local_object_id, class_id),
        source_type=source_type,
        source_id=Path(source_id).name,
        frame_number=int(frame_number),
        local_object_id=int(local_object_id),
        class_id=int(class_id),
        class_name=str(class_name),
        confidence=round(float(confidence), 6),
        x_min=x_min,
        y_min=y_min,
        x_max=x_max,
        y_max=y_max,
        width=width,
        height=height,
        area_pixels=area_pixels,
        frame_width=frame_width,
        frame_height=frame_height,
        bbox_area_ratio=round(bbox_area_ratio, 8),
        center_x=round(center_x, 4),
        center_y=round(center_y, 4),
        center_x_norm=round(center_x_norm, 8),
        center_y_norm=round(center_y_norm, 8),
        position_region=position_region(center_x_norm, center_y_norm),
        dominant_color_name=color_name,
        dom_r=dom_r,
        dom_g=dom_g,
        dom_b=dom_b,
        timestamp_sec=round(0.0 if fps <= 0 else frame_number / fps, 4),
        fps=round(float(fps), 4),
        ingestion_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        has_backpack=bool(flags.get("has_backpack", False)),
        has_cellphone=bool(flags.get("has_cellphone", False)),
        nearby_objects_count=int(flags.get("nearby_objects_count", 0)),
    )


def draw_detection(frame_bgr: np.ndarray, record: DetectionRecord) -> np.ndarray:
    """Dibuja la caja y etiqueta de una detección sobre un frame."""
    import cv2

    cv2.rectangle(frame_bgr, (record.x_min, record.y_min), (record.x_max, record.y_max), (0, 255, 0), 2)
    label = f"{record.class_name} {record.confidence:.2f}"
    cv2.putText(frame_bgr, label, (record.x_min, max(20, record.y_min - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return frame_bgr
