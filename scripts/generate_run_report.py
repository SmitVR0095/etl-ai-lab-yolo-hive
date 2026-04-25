#!/usr/bin/env python3
"""Genera un reporte Markdown de la última ejecución YOLO + HDFS + Hive."""
from __future__ import annotations

import argparse
import csv
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
        return proc.returncode, (proc.stdout or proc.stderr or "").strip()
    except FileNotFoundError as exc:
        return 127, str(exc)


def read_csv_summary(csv_path: Path) -> dict[str, object]:
    if not csv_path.exists():
        return {"exists": False, "records": 0, "sources": [], "source_type_counts": {}, "class_counts": {}}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return {
        "exists": True,
        "records": len(rows),
        "sources": sorted({r.get("source_id", "") for r in rows if r.get("source_id")}),
        "source_type_counts": dict(Counter(r.get("source_type", "") for r in rows)),
        "class_counts": dict(Counter(r.get("class_name", "") for r in rows)),
    }


def md_table_from_counter(title: str, data: dict[str, int]) -> str:
    if not data:
        return f"### {title}\n\nSin datos.\n"
    lines = [f"### {title}", "", "| Valor | Total |", "|---|---:|"]
    for key, value in sorted(data.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| {key or 'SIN_VALOR'} | {value} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera reporte de ejecución YOLO + Hive")
    parser.add_argument("--csv", default="data/staging/yolo_detections.csv")
    parser.add_argument("--hdfs-stage", default="/projects/yolo_objects/staging")
    parser.add_argument("--hive-url", default="jdbc:hive2://localhost:10000/yolo_project")
    parser.add_argument("--hive-user", default="smit_vr")
    parser.add_argument("--output-dir", default="reports")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"resumen_ejecucion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    csv_summary = read_csv_summary(Path(args.csv))
    hdfs_count_code, hdfs_count_out = run_cmd(["bash", "-lc", f"hdfs dfs -cat {args.hdfs_stage}/* 2>/dev/null | wc -l"])
    _, hdfs_ls_out = run_cmd(["bash", "-lc", f"hdfs dfs -ls {args.hdfs_stage} 2>/dev/null | tail -n +2"])
    _, hive_out = run_cmd([
        "beeline", "-u", args.hive_url, "-n", args.hive_user,
        "-e", "SELECT source_id, class_name, confidence FROM yolo_objects LIMIT 20;",
    ])

    sources = csv_summary["sources"]
    source_preview = "\n".join(f"- {s}" for s in sources[:30]) if sources else "Sin fuentes detectadas."

    content = f"""# Reporte de ejecución YOLO + HDFS + Hive

**Fecha de generación:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. Resumen general

| Indicador | Valor |
|---|---:|
| CSV existe | {csv_summary['exists']} |
| Registros en CSV | {csv_summary['records']} |
| Fuentes únicas procesadas | {len(sources)} |
| Registros HDFS estimados | {hdfs_count_out if hdfs_count_code == 0 else 'No disponible'} |

## 2. Rutas principales

| Recurso | Ruta |
|---|---|
| CSV staging | `{args.csv}` |
| HDFS staging | `{args.hdfs_stage}` |
| Hive URL | `{args.hive_url}` |
| Tabla Hive | `yolo_project.yolo_objects` |

{md_table_from_counter('Conteo por tipo de fuente', csv_summary['source_type_counts'])}

{md_table_from_counter('Conteo por clase detectada', csv_summary['class_counts'])}

## 5. Fuentes procesadas

{source_preview}

## 6. Archivos en HDFS

```text
{hdfs_ls_out or 'Sin salida HDFS disponible.'}
```

## 7. Muestra Hive

```text
{hive_out or 'Sin salida Hive disponible.'}
```

## 8. Observación

Este reporte se genera automáticamente con `make report-run`, `make demo`, `make refresh-images`, `make refresh-videos` o `make run-review`.
"""
    report_path.write_text(content, encoding="utf-8")
    print(f"✅ Reporte generado: {report_path}")


if __name__ == "__main__":
    main()
