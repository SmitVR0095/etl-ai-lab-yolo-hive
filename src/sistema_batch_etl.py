"""Sistema Batch / ETL: CSV local de YOLO hacia Hive sin duplicados.

Este sistema usa Python puro con pandas, HDFS CLI y Beeline.
No utiliza PySpark.

Responsabilidades:
- Leer el CSV generado por el sistema de clasificación YOLO.
- Validar columnas obligatorias.
- Limpiar valores inconsistentes.
- Eliminar duplicados por detection_id.
- Generar lotes por fuente y ventana de 10 segundos.
- Subir lotes a HDFS.
- Cargar lotes a Hive.
- Mantener checkpoint local para evitar reprocesamiento.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import pandas as pd

try:
    from console_utils import (
        error,
        file_ok,
        hdfs_msg,
        hive_msg,
        info,
        step,
        success,
        summary,
        warning,
    )
except ImportError:
    # Fallback para que el script siga funcionando aunque console_utils.py no exista.
    def step(message: str) -> None:
        print(f"\n🚀 {message}")

    def info(message: str) -> None:
        print(f"ℹ️  {message}")

    def success(message: str) -> None:
        print(f"✅ {message}")

    def warning(message: str) -> None:
        print(f"⚠️  {message}")

    def error(message: str) -> None:
        print(f"❌ {message}")

    def file_ok(path: str) -> None:
        print(f"📄 Archivo generado/actualizado: {path}")

    def hdfs_msg(message: str) -> None:
        print(f"🐘 {message}")

    def hive_msg(message: str) -> None:
        print(f"🐝 {message}")

    def summary(title: str, items: dict[str, object]) -> None:
        print(f"\n📊 {title}")
        for key, value in items.items():
            print(f"   {key}: {value}")


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
        info(f"No existe checkpoint previo. Se procesarán detecciones nuevas desde cero: {path}")
        return set()

    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        processed_ids = set(payload.get("processed_detection_ids", []))
        success(f"Checkpoint leído correctamente. Detecciones ya procesadas: {len(processed_ids)}")
        return processed_ids
    except json.JSONDecodeError as exc:
        warning(f"Checkpoint inválido o corrupto: {path}. Se ignorará para esta ejecución. Detalle: {exc}")
        return set()


def write_checkpoint(path: Path, processed_ids: set[str]) -> None:
    """Guarda checkpoint de detecciones procesadas."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump({"processed_detection_ids": sorted(processed_ids)}, file, indent=2)
    file_ok(str(path))


def extract_csv(input_csv: Path) -> pd.DataFrame:
    """Extrae detecciones desde CSV local."""
    if not input_csv.exists():
        error(f"No existe el CSV de staging: {input_csv}")
        raise FileNotFoundError(f"No existe el CSV de staging: {input_csv}")

    info(f"Leyendo CSV de entrada: {input_csv}")
    df = pd.read_csv(input_csv)
    success(f"CSV leído correctamente. Registros encontrados: {len(df)}")
    return df


def clean_and_transform(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia, castea y genera ventanas de 10 segundos para videos."""
    step("Limpiando y transformando datos YOLO")

    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        error(f"Columnas faltantes en CSV: {sorted(missing)}")
        raise ValueError(f"Columnas faltantes en CSV: {sorted(missing)}")

    initial_rows = len(df)
    out = df[REQUIRED_COLUMNS].copy()

    before_required = len(out)
    out = out.dropna(subset=["detection_id", "source_type", "source_id", "class_name"])
    removed_required = before_required - len(out)

    before_duplicates = len(out)
    out = out.drop_duplicates(subset=["detection_id"], keep="first")
    after = len(out)
    removed_duplicates = before_duplicates - after
    
    info(f"Duplicados eliminados: {removed_duplicates}")
    info(f"Registros únicos para procesar: {after}")
    
    numeric_int = [
        "frame_number", "local_object_id", "class_id", "x_min", "y_min", "x_max", "y_max",
        "width", "height", "area_pixels", "frame_width", "frame_height", "dom_r", "dom_g", "dom_b",
        "nearby_objects_count",
    ]
    numeric_float = [
        "confidence", "bbox_area_ratio", "center_x", "center_y",
        "center_x_norm", "center_y_norm", "timestamp_sec", "fps",
    ]

    for col in numeric_int:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)

    for col in numeric_float:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0).astype(float)

    before_rules = len(out)
    out = out[(out["confidence"] >= 0) & (out["confidence"] <= 1)]
    out = out[(out["width"] > 0) & (out["height"] > 0)]
    out = out[(out["x_max"] > out["x_min"]) & (out["y_max"] > out["y_min"])]
    removed_rules = before_rules - len(out)

    out["has_backpack"] = out["has_backpack"].astype(str).str.lower().isin(["true", "1", "yes", "si", "sí"])
    out["has_cellphone"] = out["has_cellphone"].astype(str).str.lower().isin(["true", "1", "yes", "si", "sí"])

    # Regla de lotes: imágenes se cargan juntas en [0,10); videos se agrupan por ventanas de 10 s.
    out["batch_window_start"] = (out["timestamp_sec"] // 10 * 10).astype(int)
    out.loc[out["source_type"] == "image", "batch_window_start"] = 0
    out["batch_window_end"] = out["batch_window_start"] + 10

    summary(
        "Resumen de limpieza",
        {
            "Registros iniciales": initial_rows,
            "Registros sin campos obligatorios": removed_required,
            "Duplicados eliminados por detection_id": removed_duplicates,
            "Registros descartados por reglas de calidad": removed_rules,
            "Registros válidos": len(out),
        },
    )

    if out.empty:
        warning("No quedaron registros válidos después de la limpieza.")

    return out[HIVE_COLUMNS]


def filter_new_records(df: pd.DataFrame, checkpoint_ids: set[str]) -> pd.DataFrame:
    """Retorna únicamente registros que no están en checkpoint."""
    if not checkpoint_ids:
        info("No hay IDs previos en checkpoint. Se tomarán todos los registros válidos.")
        return df.copy()

    before = len(df)
    new_df = df[~df["detection_id"].isin(checkpoint_ids)].copy()
    skipped = before - len(new_df)

    info(f"Registros omitidos por checkpoint: {skipped}")
    info(f"Registros nuevos para cargar: {len(new_df)}")
    return new_df


def write_local_batches(df: pd.DataFrame, output_dir: Path) -> list[Path]:
    """Escribe CSV limpios por fuente y ventana de 10 segundos."""
    step("Generando lotes locales para HDFS/Hive")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Limpieza de lotes previos para evitar confusiones visuales en la revisión.
    for old_file in output_dir.glob("batch_*.csv"):
        old_file.unlink()

    batch_files: list[Path] = []
    grouped = df.groupby(["source_type", "source_id", "batch_window_start", "batch_window_end"], dropna=False)

    for (source_type, source_id, start, end), batch in grouped:
        safe_source = str(source_id).replace("/", "_").replace("\\", "_").replace(" ", "_")
        file_path = output_dir / f"batch_{source_type}_{safe_source}_{int(start)}_{int(end)}.csv"
        batch.to_csv(file_path, index=False, header=False)
        batch_files.append(file_path)
        file_ok(str(file_path))

    success(f"Lotes generados correctamente: {len(batch_files)}")
    return batch_files


def run_command(command: list[str], dry_run: bool = False) -> None:
    """Ejecuta un comando del sistema o lo muestra en modo simulación."""
    printable = " ".join(command)
    if dry_run:
        warning(f"[DRY-RUN] {printable}")
        return

    info(f"Ejecutando comando: {printable}")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        error(f"Falló el comando con código {exc.returncode}: {printable}")
        raise


def load_batches_to_hive(batch_files: list[Path], hdfs_dir: str, table: str, beeline_url: str, dry_run: bool) -> None:
    """Carga lotes CSV a HDFS y luego a una tabla staging/final de Hive."""
    if not batch_files:
        warning("No hay archivos batch para cargar a Hive.")
        return

    step("Cargando lotes a HDFS y Hive")
    hdfs_msg(f"Directorio HDFS destino: {hdfs_dir}")
    hive_msg(f"Tabla Hive destino: {table}")
    hive_msg(f"URL Beeline: {beeline_url}")

    run_command(["hdfs", "dfs", "-mkdir", "-p", hdfs_dir], dry_run)

    for idx, file_path in enumerate(batch_files, start=1):
        hdfs_target = f"{hdfs_dir.rstrip('/')}/{file_path.name}"
        hdfs_msg(f"[{idx}/{len(batch_files)}] Subiendo lote a HDFS: {file_path.name}")
        run_command(["hdfs", "dfs", "-put", "-f", str(file_path), hdfs_target], dry_run)

        hive_sql = f"LOAD DATA INPATH '{hdfs_target}' INTO TABLE {table};"
        hive_msg(f"[{idx}/{len(batch_files)}] Cargando lote en Hive: {file_path.name}")
        run_command(["beeline", "-u", beeline_url, "-e", hive_sql], dry_run)

    success("Carga de lotes a HDFS/Hive finalizada correctamente.")


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

    step("Iniciando proceso Batch ETL: CSV → HDFS → Hive")
    info(f"CSV de entrada: {args.input_csv}")
    info(f"Directorio batch local: {args.output_dir}")
    info(f"Checkpoint: {args.checkpoint}")
    hdfs_msg(f"Directorio HDFS: {args.hdfs_dir}")
    hive_msg(f"Tabla Hive: {args.table}")
    hive_msg(f"Beeline URL: {args.beeline_url}")

    input_csv = Path(args.input_csv)
    checkpoint_path = Path(args.checkpoint)

    processed_ids = read_checkpoint(checkpoint_path)

    raw_df = extract_csv(input_csv)
    clean_df = clean_and_transform(raw_df)
    new_df = filter_new_records(clean_df, processed_ids)

    if new_df.empty:
        warning("No hay detecciones nuevas para cargar a Hive.")
        summary(
            "Resumen ETL",
            {
                "CSV entrada": str(input_csv),
                "Registros leídos": len(raw_df),
                "Registros válidos": len(clean_df),
                "Registros nuevos": 0,
                "Estado": "Sin carga por checkpoint o CSV vacío",
            },
        )
        return

    batch_files = write_local_batches(new_df, Path(args.output_dir))
    load_batches_to_hive(batch_files, args.hdfs_dir, args.table, args.beeline_url, args.dry_run)

    processed_ids.update(new_df["detection_id"].astype(str).tolist())
    write_checkpoint(checkpoint_path, processed_ids)

    summary(
        "Resumen ETL",
        {
            "CSV entrada": str(input_csv),
            "Registros leídos": len(raw_df),
            "Registros válidos": len(clean_df),
            "Registros cargados": len(new_df),
            "Lotes generados": len(batch_files),
            "HDFS destino": args.hdfs_dir,
            "Tabla Hive": args.table,
            "Checkpoint": str(checkpoint_path),
        },
    )

    success("Proceso Batch ETL finalizado correctamente.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        error(f"Proceso Batch ETL finalizó con error: {exc}")
        raise
