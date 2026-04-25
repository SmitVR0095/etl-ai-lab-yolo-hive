"""Sistema Batch / ETL: CSV local de YOLO hacia Hive sin duplicados.

Este sistema usa Python puro con pandas y beeline. No utiliza PySpark.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = [
    "detection_id", "source_type", "source_id", "frame_number", "local_object_id",
    "class_id", "class_name", "confidence", "x_min", "y_min", "x_max", "y_max",
    "width", "height", "area_pixels", "frame_width", "frame_height", "bbox_area_ratio",
    "center_x", "center_y", "center_x_norm", "center_y_norm", "position_region",
    "dominant_color_name", "dom_r", "dom_g", "dom_b", "timestamp_sec", "fps",
    "ingestion_date", "has_backpack", "has_cellphone", "nearby_objects_count",
]

HIVE_COLUMNS = REQUIRED_COLUMNS + ["batch_window_start", "batch_window_end"]


def read_checkpoint(path: Path) -> set[str]:
    """Lee detection_id ya cargados desde el checkpoint local."""
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return set(payload.get("processed_detection_ids", []))


def write_checkpoint(path: Path, processed_ids: set[str]) -> None:
    """Guarda checkpoint de detecciones procesadas."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump({"processed_detection_ids": sorted(processed_ids)}, file, indent=2)


def extract_csv(input_csv: Path) -> pd.DataFrame:
    """Extrae detecciones desde CSV local."""
    if not input_csv.exists():
        raise FileNotFoundError(f"No existe el CSV de staging: {input_csv}")
    return pd.read_csv(input_csv)


def clean_and_transform(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia, castea y genera ventanas de 10 segundos para videos."""
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Columnas faltantes en CSV: {sorted(missing)}")

    out = df[REQUIRED_COLUMNS].copy()
    out = out.dropna(subset=["detection_id", "source_type", "source_id", "class_name"])
    out = out.drop_duplicates(subset=["detection_id"], keep="first")

    numeric_int = [
        "frame_number", "local_object_id", "class_id", "x_min", "y_min", "x_max", "y_max",
        "width", "height", "area_pixels", "frame_width", "frame_height", "dom_r", "dom_g", "dom_b",
        "nearby_objects_count",
    ]
    numeric_float = ["confidence", "bbox_area_ratio", "center_x", "center_y", "center_x_norm", "center_y_norm", "timestamp_sec", "fps"]

    for col in numeric_int:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)
    for col in numeric_float:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0).astype(float)

    out = out[(out["confidence"] >= 0) & (out["confidence"] <= 1)]
    out = out[(out["width"] > 0) & (out["height"] > 0)]
    out = out[(out["x_max"] > out["x_min"]) & (out["y_max"] > out["y_min"])]

    out["has_backpack"] = out["has_backpack"].astype(str).str.lower().isin(["true", "1", "yes", "si", "sí"])
    out["has_cellphone"] = out["has_cellphone"].astype(str).str.lower().isin(["true", "1", "yes", "si", "sí"])

    # Regla de lotes: imágenes se cargan juntas en [0,10); videos se agrupan por ventanas de 10 s.
    out["batch_window_start"] = (out["timestamp_sec"] // 10 * 10).astype(int)
    out.loc[out["source_type"] == "image", "batch_window_start"] = 0
    out["batch_window_end"] = out["batch_window_start"] + 10
    return out[HIVE_COLUMNS]


def filter_new_records(df: pd.DataFrame, checkpoint_ids: set[str]) -> pd.DataFrame:
    """Retorna únicamente registros que no están en checkpoint."""
    return df[~df["detection_id"].isin(checkpoint_ids)].copy()


def write_local_batches(df: pd.DataFrame, output_dir: Path) -> list[Path]:
    """Escribe CSV limpios por fuente y ventana de 10 segundos."""
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_files: list[Path] = []
    grouped = df.groupby(["source_type", "source_id", "batch_window_start", "batch_window_end"], dropna=False)
    for (source_type, source_id, start, end), batch in grouped:
        safe_source = str(source_id).replace("/", "_").replace(" ", "_")
        file_path = output_dir / f"batch_{source_type}_{safe_source}_{int(start)}_{int(end)}.csv"
        batch.to_csv(file_path, index=False, header=False)
        batch_files.append(file_path)
    return batch_files


def run_command(command: list[str], dry_run: bool = False) -> None:
    """Ejecuta un comando del sistema o lo muestra en modo simulación."""
    print("$ " + " ".join(command))
    if not dry_run:
        subprocess.run(command, check=True)


def load_batches_to_hive(batch_files: list[Path], hdfs_dir: str, table: str, beeline_url: str, dry_run: bool) -> None:
    """Carga lotes CSV a HDFS y luego a una tabla staging/final de Hive."""
    for file_path in batch_files:
        hdfs_target = f"{hdfs_dir.rstrip('/')}/{file_path.name}"
        run_command(["hdfs", "dfs", "-mkdir", "-p", hdfs_dir], dry_run)
        run_command(["hdfs", "dfs", "-put", "-f", str(file_path), hdfs_target], dry_run)
        hive_sql = (
            f"LOAD DATA INPATH '{hdfs_target}' INTO TABLE {table};"
        )
        run_command(["beeline", "-u", beeline_url, "-e", hive_sql], dry_run)


def main() -> None:
    """Punto de entrada CLI del sistema batch ETL."""
    parser = argparse.ArgumentParser(description="ETL CSV YOLO hacia Hive sin duplicados")
    parser.add_argument("--input-csv", default="data/staging/yolo_detections.csv")
    parser.add_argument("--output-dir", default="data/processed/hive_batches")
    parser.add_argument("--checkpoint", default="checkpoints/yolo_hive_checkpoint.json")
    parser.add_argument("--hdfs-dir", default="/projects/yolo_objects/staging")
    parser.add_argument("--table", default="yolo_objects_csv_stage")
    parser.add_argument("--beeline-url", default="jdbc:hive2://localhost:10000/default")
    parser.add_argument("--dry-run", action="store_true", help="Genera lotes sin ejecutar HDFS/Hive")
    args = parser.parse_args()

    input_csv = Path(args.input_csv)
    checkpoint_path = Path(args.checkpoint)
    processed_ids = read_checkpoint(checkpoint_path)

    raw_df = extract_csv(input_csv)
    clean_df = clean_and_transform(raw_df)
    new_df = filter_new_records(clean_df, processed_ids)

    if new_df.empty:
        print("No hay detecciones nuevas para cargar a Hive.")
        return

    batch_files = write_local_batches(new_df, Path(args.output_dir))
    print(f"Lotes generados: {len(batch_files)}")
    load_batches_to_hive(batch_files, args.hdfs_dir, args.table, args.beeline_url, args.dry_run)

    processed_ids.update(new_df["detection_id"].astype(str).tolist())
    write_checkpoint(checkpoint_path, processed_ids)
    print(f"Checkpoint actualizado: {checkpoint_path}")


if __name__ == "__main__":
    main()
