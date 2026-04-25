"""Sistema de Clasificación YOLO: imágenes, videos y cámara a CSV local.

Restricción del proyecto: este sistema NO se conecta a Hive. Su única salida persistente
son archivos CSV en la capa de staging.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
from ultralytics import YOLO

from console_utils import (
    camera_msg,
    error,
    file_ok,
    image_msg,
    info,
    model_msg,
    step,
    success,
    summary,
    video_msg,
    warning,
)
from yolo_features import CSV_COLUMNS, build_record, draw_detection

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def append_records(csv_path: Path, records: list[dict]) -> None:
    """Agrega registros al CSV de staging, creando cabecera si no existe."""
    if not records:
        return

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = csv_path.exists()

    with csv_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(records)


def reset_csv(csv_path: Path) -> None:
    """Elimina el CSV de staging para regenerarlo limpio en cada ejecución."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if csv_path.exists():
        csv_path.unlink()
        info(f"CSV anterior eliminado: {csv_path}")
    else:
        info(f"No existe CSV previo. Se generará uno nuevo en: {csv_path}")


def iter_files(input_dir: Path, extensions: set[str]) -> list[Path]:
    """Lista archivos válidos de forma ordenada desde una carpeta."""
    if not input_dir.exists():
        warning(f"No existe la carpeta de entrada: {input_dir}")
        return []
    return sorted(path for path in input_dir.iterdir() if path.suffix.lower() in extensions)


def detect_frame(
    model: YOLO,
    frame,
    source_type: str,
    source_id: str,
    frame_number: int,
    fps: float,
    conf: float,
) -> tuple[list[dict], object]:
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
    step("Procesamiento de imágenes")
    image_msg(f"Buscando imágenes en: {image_dir}")

    image_files = iter_files(image_dir, IMAGE_EXTENSIONS)
    info(f"Total de imágenes encontradas: {len(image_files)}")

    if not image_files:
        warning("No se encontraron imágenes para procesar.")
        return 0

    total = 0
    annotated_dir.mkdir(parents=True, exist_ok=True)

    for index, image_path in enumerate(image_files, start=1):
        image_msg(f"[{index}/{len(image_files)}] Procesando imagen: {image_path.name}")

        frame = cv2.imread(str(image_path))
        if frame is None:
            warning(f"No se pudo leer imagen: {image_path}")
            continue

        records, annotated = detect_frame(model, frame, "image", image_path.name, 0, 0.0, conf)
        append_records(output_csv, records)

        annotated_path = annotated_dir / image_path.name
        cv2.imwrite(str(annotated_path), annotated)

        total += len(records)
        success(f"Imagen {image_path.name}: {len(records)} detecciones")
        file_ok(str(annotated_path))

    summary(
        "Resumen de imágenes",
        {
            "Imágenes procesadas": len(image_files),
            "Detecciones generadas": total,
            "CSV": output_csv,
            "Salida anotada": annotated_dir,
        },
    )
    return total


def process_videos(
    model: YOLO,
    video_dir: Path,
    output_csv: Path,
    annotated_dir: Path,
    conf: float,
    every_n_frames: int,
) -> int:
    """Procesa videos por muestreo de frames y genera registros CSV."""
    step("Procesamiento de videos")
    video_msg(f"Buscando videos en: {video_dir}")

    video_files = iter_files(video_dir, VIDEO_EXTENSIONS)
    info(f"Total de videos encontrados: {len(video_files)}")

    if not video_files:
        warning("No se encontraron videos para procesar.")
        return 0

    total = 0
    annotated_dir.mkdir(parents=True, exist_ok=True)

    for index, video_path in enumerate(video_files, start=1):
        video_msg(f"[{index}/{len(video_files)}] Procesando video: {video_path.name}")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            warning(f"No se pudo abrir video: {video_path}")
            continue

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
        out_path = annotated_dir / f"annotated_{video_path.stem}.mp4"
        writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

        frame_number = 0
        video_detections = 0

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            if frame_number % every_n_frames == 0:
                records, annotated = detect_frame(model, frame, "video", video_path.name, frame_number, fps, conf)
                append_records(output_csv, records)
                video_detections += len(records)
                total += len(records)
                writer.write(annotated)

            frame_number += 1

        writer.release()
        cap.release()

        success(
            f"Video {video_path.name}: frames={frame_number}, "
            f"detecciones={video_detections}, muestreo cada {every_n_frames} frame(s)"
        )
        file_ok(str(out_path))

    summary(
        "Resumen de videos",
        {
            "Videos procesados": len(video_files),
            "Detecciones generadas": total,
            "CSV": output_csv,
            "Salida anotada": annotated_dir,
        },
    )
    return total


def process_camera(model: YOLO, camera_index: int, output_csv: Path, conf: float, every_n_frames: int) -> None:
    """Ejecuta detección en tiempo real desde cámara USB/CSI visible para OpenCV."""
    step("Procesamiento de cámara en tiempo real")
    camera_msg(f"Abriendo cámara con índice: {camera_index}")

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir la cámara con índice {camera_index}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_number = 0
    total = 0

    info("Presiona 'q' para salir.")

    while True:
        ok, frame = cap.read()
        if not ok:
            warning("No se pudo leer más frames desde la cámara.")
            break

        if frame_number % every_n_frames == 0:
            records, annotated = detect_frame(model, frame, "video", f"camera_{camera_index}", frame_number, fps, conf)
            append_records(output_csv, records)
            total += len(records)
            cv2.imshow("YOLO Real Time", annotated)
        else:
            cv2.imshow("YOLO Real Time", frame)

        frame_number += 1

        if cv2.waitKey(1) & 0xFF == ord("q"):
            info("Salida solicitada por el usuario.")
            break

    cap.release()
    cv2.destroyAllWindows()

    summary(
        "Resumen de cámara",
        {
            "Frames leídos": frame_number,
            "Detecciones generadas": total,
            "CSV": output_csv,
        },
    )


def main() -> None:
    """Punto de entrada CLI del sistema de clasificación."""
    parser = argparse.ArgumentParser(description="Sistema de clasificación YOLO hacia CSV local")
    parser.add_argument("--model", default="models/yolov8n.pt", help="Ruta al modelo YOLO .pt")
    parser.add_argument("--images", default="data/raw/images", help="Carpeta de imágenes")
    parser.add_argument("--videos", default="data/raw/videos", help="Carpeta de videos")
    parser.add_argument("--output-csv", default="data/staging/yolo_detections.csv", help="CSV de staging")
    parser.add_argument(
        "--append-csv",
        action="store_true",
        help="No borra el CSV antes de procesar; agrega filas al archivo existente",
    )
    parser.add_argument("--annotated-dir", default="data/processed/annotated", help="Salida de imágenes/videos anotados")
    parser.add_argument("--conf", type=float, default=0.35, help="Confianza mínima YOLO")
    parser.add_argument("--every-n-frames", type=int, default=5, help="Muestreo para video/cámara")
    parser.add_argument("--mode", choices=["images", "videos", "all", "camera"], default="all")
    parser.add_argument("--camera-index", type=int, default=0)
    args = parser.parse_args()

    step("Iniciando sistema de clasificación YOLO")
    info(f"Modo de ejecución: {args.mode}")
    info(f"Confianza mínima: {args.conf}")
    info(f"CSV de salida: {args.output_csv}")

    model_path = Path(args.model)
    if not model_path.exists():
        error(f"No se encontró el modelo YOLO en: {model_path}")
        raise FileNotFoundError(f"No se encontró el modelo YOLO en: {model_path}")

    model_msg(f"Cargando modelo YOLO desde: {model_path}")
    model = YOLO(str(model_path))
    success("Modelo YOLO cargado correctamente.")

    output_csv = Path(args.output_csv)
    annotated_dir = Path(args.annotated_dir)

    if not args.append_csv:
        reset_csv(output_csv)
    else:
        warning("Modo append activo: el CSV existente no será eliminado.")

    total_images = 0
    total_videos = 0

    if args.mode in {"images", "all"}:
        total_images = process_images(model, Path(args.images), output_csv, annotated_dir / "images", args.conf)

    if args.mode in {"videos", "all"}:
        total_videos = process_videos(
            model,
            Path(args.videos),
            output_csv,
            annotated_dir / "videos",
            args.conf,
            args.every_n_frames,
        )

    if args.mode == "camera":
        process_camera(model, args.camera_index, output_csv, args.conf, args.every_n_frames)

    file_ok(str(output_csv))
    success("Detección YOLO finalizada correctamente.")

    summary(
        "Resumen general de clasificación",
        {
            "Modo": args.mode,
            "Detecciones en imágenes": total_images,
            "Detecciones en videos": total_videos,
            "CSV": output_csv,
            "Modelo": model_path,
        },
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        error(f"Proceso de clasificación finalizó con error: {exc}")
        raise
