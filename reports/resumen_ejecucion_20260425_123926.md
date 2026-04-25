# Reporte de ejecución YOLO + HDFS + Hive

- Fecha de ejecución: 2026-04-25 12:39:32
- Proyecto: /home/smit_vr/cursobsgetl/codigo/etl-ai-lab
- Modelo: models/yolov8n.pt
- Confianza mínima: 0.35
- Every N frames: 5

## Resumen

| Métrica | Valor |
|---|---:|
| Imágenes disponibles | 20 |
| Videos disponibles | 20 |
| Registros en CSV | 1324 |
| Archivos en HDFS staging | 5 |

## Rutas

- CSV: `data/staging/yolo_detections.csv`
- HDFS staging: `/projects/yolo_objects/staging`
- Hive DB: `yolo_project`
- Tabla final: `yolo_objects`
- Muestra Hive guardada en: `reports/hive_sample_20260425_123926.txt`
