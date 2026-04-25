#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida el CSV generado por YOLO")
    parser.add_argument("--csv", default="data/staging/yolo_detections.csv")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    required = {"detection_id", "source_id", "class_name", "confidence"}
    print(f"🔍 Validando CSV: {csv_path}")

    if not csv_path.exists():
        print(f"❌ No existe el CSV: {csv_path}", file=sys.stderr)
        sys.exit(1)

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            print("❌ El CSV está vacío.", file=sys.stderr)
            sys.exit(1)
        missing = required - set(header)
        if missing:
            print(f"❌ Faltan columnas requeridas: {sorted(missing)}", file=sys.stderr)
            sys.exit(1)
        rows = sum(1 for _ in reader)

    if rows <= 0:
        print("❌ El CSV no contiene registros de detección.", file=sys.stderr)
        sys.exit(1)

    print(f"✅ CSV válido. Registros de detección: {rows}")


if __name__ == "__main__":
    main()
