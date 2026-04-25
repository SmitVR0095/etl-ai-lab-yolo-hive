"""Sistema de Clasificación YOLO: imágenes, videos y cámara a CSV local.

Restricción del proyecto: este sistema NO se conecta a Hive. Su única salida persistente
son archivos CSV en la capa de staging.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable

import cv2
from ultralytics import YOLO

from yolo_features import CSV_COLUMNS, build_record, draw_detection

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def append_records(csv_path: Path, records: list[dict]) -> None:
    """Agrega registros al CSV de staging, creando cabecera si no existe."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(records)


def iter_files(input_dir: Path, extensions: set[str]) -> Iterable[Path]:
    """Lista archivos válidos de forma ordenada desde una carpeta."""
    if not input_dir.exists():
        return []
    return sorted(path for path in input_dir.iterdir() if path.suffix.lower() in extensions)


def detect_frame(model: YOLO, frame, source_type: str, source_id: str, frame_number: int, fps: float, conf: float) -> tuple[list[dict], object]:
    """Ejecuta YOLO sobre un frame y retorna registros enriquecidos y frame anotado."""
    results = model.predict(frame, conf=conf, verbose=False)
    records = []
    annotated = frame.copy()

    for result in results:
        names = result.names
        boxes = result.boxes
        if boxes is None:
            continue
        for local_object_id, box in enumerate(boxes):
            class_id = int(box.cls[0].item())
            class_name = str(names.get(class_id, class_id))
            confidence = float(box.conf[0].item())
            xyxy = tuple(float(v) for v in box.xyxy[0].tolist())

            record = build_record(
                frame_bgr=frame,
                source_type=source_type,
                source_id=source_id,
                frame_number=frame_number,
                local_object_id=local_object_id,
                class_id=class_id,
                class_name=class_name,
                confidence=confidence,
                xyxy=xyxy,
                fps=fps,
            )
            records.append(record.to_dict())
            annotated = draw_detection(annotated, record)
    return records, annotated


def process_images(model: YOLO, image_dir: Path, output_csv: Path, annotated_dir: Path, conf: float) -> int:
    """Procesa todas las imágenes de una carpeta y genera registros CSV."""
    total = 0
    annotated_dir.mkdir(parents=True, exist_ok=True)
    for image_path in iter_files(image_dir, IMAGE_EXTENSIONS):
        frame = cv2.imread(str(image_path))
        if frame is None:
            print(f"[WARN] No se pudo leer imagen: {image_path}")
            continue
        records, annotated = detect_frame(model, frame, "image", image_path.name, 0, 0.0, conf)
        append_records(output_csv, records)
        cv2.imwrite(str(annotated_dir / image_path.name), annotated)
        total += len(records)
        print(f"[OK] Imagen {image_path.name}: {len(records)} detecciones")
    return total


def process_videos(model: YOLO, video_dir: Path, output_csv: Path, annotated_dir: Path, conf: float, every_n_frames: int) -> int:
    """Procesa videos por muestreo de frames y genera registros CSV."""
    total = 0
    annotated_dir.mkdir(parents=True, exist_ok=True)
    for video_path in iter_files(video_dir, VIDEO_EXTENSIONS):
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"[WARN] No se pudo abrir video: {video_path}")
            continue

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
        out_path = annotated_dir / f"annotated_{video_path.stem}.mp4"
        writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

        frame_number = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_number % every_n_frames == 0:
                records, annotated = detect_frame(model, frame, "video", video_path.name, frame_number, fps, conf)
                append_records(output_csv, records)
                total += len(records)
                writer.write(annotated)
            frame_number += 1

        writer.release()
        cap.release()
        print(f"[OK] Video {video_path.name}: frames={frame_number}, detecciones acumuladas={total}")
    return total


def process_camera(model: YOLO, camera_index: int, output_csv: Path, conf: float, every_n_frames: int) -> None:
    """Ejecuta detección en tiempo real desde cámara USB/CSI visible para OpenCV."""
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir la cámara con índice {camera_index}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_number = 0
    print("Presiona 'q' para salir.")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_number % every_n_frames == 0:
            records, annotated = detect_frame(model, frame, "video", f"camera_{camera_index}", frame_number, fps, conf)
            append_records(output_csv, records)
            cv2.imshow("YOLO Real Time", annotated)
        else:
            cv2.imshow("YOLO Real Time", frame)
        frame_number += 1
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def main() -> None:
    """Punto de entrada CLI del sistema de clasificación."""
    parser = argparse.ArgumentParser(description="Sistema de clasificación YOLO hacia CSV local")
    parser.add_argument("--model", default="models/yolov8n.pt", help="Ruta al modelo YOLO .pt")
    parser.add_argument("--images", default="data/raw/images", help="Carpeta de imágenes")
    parser.add_argument("--videos", default="data/raw/videos", help="Carpeta de videos")
    parser.add_argument("--output-csv", default="data/staging/yolo_detections.csv", help="CSV de staging")
    parser.add_argument("--annotated-dir", default="data/processed/annotated", help="Salida de imágenes/videos anotados")
    parser.add_argument("--conf", type=float, default=0.35, help="Confianza mínima YOLO")
    parser.add_argument("--every-n-frames", type=int, default=5, help="Muestreo para video/cámara")
    parser.add_argument("--mode", choices=["images", "videos", "all", "camera"], default="all")
    parser.add_argument("--camera-index", type=int, default=0)
    args = parser.parse_args()

    model = YOLO(args.model)
    output_csv = Path(args.output_csv)
    annotated_dir = Path(args.annotated_dir)

    if args.mode in {"images", "all"}:
        process_images(model, Path(args.images), output_csv, annotated_dir / "images", args.conf)
    if args.mode in {"videos", "all"}:
        process_videos(model, Path(args.videos), output_csv, annotated_dir / "videos", args.conf, args.every_n_frames)
    if args.mode == "camera":
        process_camera(model, args.camera_index, output_csv, args.conf, args.every_n_frames)


if __name__ == "__main__":
    main()
